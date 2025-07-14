import base64
import io
import os
import re
import traceback
from datetime import datetime

import requests
from PIL import Image, ImageFilter
from PIL.ExifTags import TAGS, GPSTAGS
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import Vehicle, Batch, Photo, Park
from ...utils.rgpd import RGPD


class Command(BaseCommand):
    help = 'Process photos and update parking database'

    def add_arguments(self, parser):
        parser.add_argument('--input-dir', type=str, required=True, help='Input directory with photos')
        parser.add_argument('--output-dir', type=str, required=True, help='Output directory for sorted photos')
        parser.add_argument('--api-key', type=str, required=True, help='PlateRecognizer API key')

    def handle(self, *args, **options):
        input_dir = options['input_dir']
        output_dir = options['output_dir']
        api_key = options['api_key']

        # Vérifier qu'il y a bien une clé publique, mais pas de clé privée
        if os.path.exists(settings.SECURITY_PRIVATE_KEY_URL):
            self.stdout.write(self.style.ERROR(
                f'La clé de chiffrement privée DOIT être stockée sur un média à part et supprimée du projet.'))
            quit()

        try:
            public_key_pem = RGPD.load_key_from_file(settings.SECURITY_PUBLIC_KEY_URL)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur avec la clé de chiffrement public {e}'))
            self.stdout.write(self.style.ERROR(
                f'La clé de chiffrement public DOIT être présent dans le projet ici : {settings.SECURITY_PUBLIC_KEY_URL}.'))
            self.stdout.write(self.style.ERROR(
                f'Pour créer des clés, utilisez la commande python manage.py make_keys --password VOTRE_MOT_DE_PASSE_SECRET'))
            quit()

        # Vérifier si le dossier d'entrée contient des photos
        photo_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.jpg', '.jpeg'))]

        if not photo_files:
            self.stdout.write(self.style.SUCCESS('Aucune photo à traiter'))
            return

        # Créer un nouveau batch
        batch = Batch.objects.create()
        self.stdout.write(self.style.SUCCESS(f'Nouveau batch créé: {batch.id}'))

        # Traiter chaque photo
        processed_vehicles = set()

        for photo_file in photo_files:
            photo_path = os.path.join(input_dir, photo_file)
            try:
                # Extraire les métadonnées EXIF
                exif_data = self.extract_exif(photo_path)

                # Reconnaître la plaque d'immatriculation
                results = self.recognize_plate(photo_path, api_key)

                if results:
                    plate_number = self.format_plate(results['plate'])
                    finger_print = RGPD.generate_fingerprint(plate_number, public_key_pem)

                    # Créer ou récupérer le véhicule
                    vehicle, created = Vehicle.objects.get_or_create(finger_print=finger_print)

                    if created:
                        vehicle.encoded_plate = RGPD.encrypt_text(plate_number, public_key_pem)
                        vehicle.save()
                        self.stdout.write(f'Nouveau véhicule: {plate_number}')

                    # Créer l'enregistrement Photo
                    photo = Photo.objects.create(
                        vehicle=vehicle,
                        batch=batch,
                        date_time=exif_data['datetime'],
                        latitude=exif_data.get('latitude'),
                        longitude=exif_data.get('longitude')
                    )

                    # Classer la photo
                    self.organize_photo(photo_path, output_dir, results['resized_img'], results['box'], vehicle.id, photo.id,
                                        exif_data['datetime'], )

                    processed_vehicles.add(finger_print)
                    self.stdout.write(f'Photo traitée: {plate_number}')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Erreur lors du traitement de {photo_file}.'))
                traceback.print_exc()
                quit()

        # Mettre à jour les stationnements
        self.update_parking_records(batch, processed_vehicles)

        self.stdout.write(self.style.SUCCESS(f'Traitement terminé. {len(processed_vehicles)} véhicules traités.'))

    def extract_exif(self, photo_path):
        """Extrait les données EXIF d'une photo"""
        with Image.open(photo_path) as img:
            exif_dict = img._getexif()

            if exif_dict is None:
                # Utiliser la date de modification du fichier si pas d'EXIF
                stat = os.stat(photo_path)
                return {
                    'datetime': datetime.fromtimestamp(stat.st_mtime),
                    'latitude': None,
                    'longitude': None
                }

            exif_data = {}

            # Extraire la date/heure
            for tag, value in exif_dict.items():
                tag_name = TAGS.get(tag, tag)
                if tag_name == 'DateTime':
                    exif_data['datetime'] = self.process_exif_datetime(value)
                elif tag_name == 'GPSInfo':
                    gps_data = {}
                    for gps_tag in value:
                        gps_tag_name = GPSTAGS.get(gps_tag, gps_tag)
                        gps_data[gps_tag_name] = value[gps_tag]

                    # Convertir les coordonnées GPS
                    if 'GPSLatitude' in gps_data and 'GPSLongitude' in gps_data:
                        lat = self.convert_gps_coordinate(gps_data['GPSLatitude'], gps_data.get('GPSLatitudeRef', 'N'))
                        lon = self.convert_gps_coordinate(gps_data['GPSLongitude'],
                                                          gps_data.get('GPSLongitudeRef', 'E'))
                        exif_data['latitude'] = lat
                        exif_data['longitude'] = lon

            # Utiliser la date de modification si pas de date EXIF
            if 'datetime' not in exif_data:
                stat = os.stat(photo_path)
                exif_data['datetime'] = datetime.fromtimestamp(stat.st_mtime)

            return exif_data

    def process_exif_datetime(self, exif_datetime_str):
        """
        Traite spécifiquement les données datetime des EXIF.
        Les photos ont généralement l'heure locale où elles ont été prises.
        """
        if not exif_datetime_str:
            return None

        # Convertir la chaîne en datetime naïf
        naive_dt = datetime.strptime(exif_datetime_str, '%Y:%m:%d %H:%M:%S')

        # Utiliser la timezone configurée dans Django
        # (qui correspond à votre timezone locale Europe/Paris)
        aware_dt = timezone.make_aware(naive_dt)

        return aware_dt

    def convert_gps_coordinate(self, coordinate, ref):
        """Convertit les coordonnées GPS en degrés décimaux"""
        degrees = float(coordinate[0])
        minutes = float(coordinate[1])
        seconds = float(coordinate[2])

        decimal = degrees + minutes / 60 + seconds / 3600

        if ref in ['S', 'W']:
            decimal = -decimal

        return decimal

    def image_to_base64(self, image, format='JPEG', quality=85):
        """
        Convertit une image PIL en string base64.
        """
        buffer = io.BytesIO()
        image.save(buffer, format=format, quality=quality)
        buffer.seek(0)

        # Encoder en base64
        img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        return img_base64

    def resize_image_keep_ratio(self, image, max_width=1980, max_height=1080):
        """
        Redimensionne une image en conservant le ratio largeur:hauteur
        pour qu'elle tienne dans les dimensions maximales spécifiées.
        """
        original_width, original_height = image.size

        # Calcul du ratio de redimensionnement
        width_ratio = max_width / original_width
        height_ratio = max_height / original_height

        # Prendre le plus petit ratio pour que l'image tienne dans les limites
        resize_ratio = min(width_ratio, height_ratio)

        # Si l'image est déjà plus petite, ne pas l'agrandir
        if resize_ratio >= 1:
            return image

        # Nouvelles dimensions
        new_width = int(original_width * resize_ratio)
        new_height = int(original_height * resize_ratio)

        # Redimensionner avec un filtre de qualité
        return image.resize((new_width, new_height), Image.LANCZOS)

    def format_plate(self, plate):
        if not plate:
            return None

        # Nettoyer la chaîne : supprimer espaces, tirets et convertir en majuscules
        plaque_clean = re.sub(r'[\s\-]', '', plate.upper())

        # Pattern pour le nouveau format (AA123AA)
        pattern_nouveau = r'^([A-Z]{2})(\d{3})([A-Z]{2})$'
        match_nouveau = re.match(pattern_nouveau, plaque_clean)

        if match_nouveau:
            # Format nouveau : AA-123-AA
            lettres1, chiffres, lettres2 = match_nouveau.groups()
            return f"{lettres1}-{chiffres}-{lettres2}"

        # Pattern pour l'ancien format (1234AA12)
        pattern_ancien = r'^(\d{1,4})([A-Z]{1,3})(\d{2})$'
        match_ancien = re.match(pattern_ancien, plaque_clean)

        if match_ancien:
            # Format ancien : 1234 AA 12
            chiffres1, lettres, chiffres2 = match_ancien.groups()
            return f"{chiffres1} {lettres} {chiffres2}"

        # Pattern pour les plaques temporaires/export (format spécial)
        pattern_temp = r'^(\d{3,4})([A-Z]{1,3})(\d{2})$'
        match_temp = re.match(pattern_temp, plaque_clean)

        if match_temp:
            chiffres1, lettres, chiffres2 = match_temp.groups()
            return f"{chiffres1} {lettres} {chiffres2}"

        return None

    def recognize_plate(self, photo_path, api_key):
        """Reconnaît la plaque d'immatriculation via PlateRecognizer"""

        with Image.open(photo_path) as img:
            # Convertir en RGB si nécessaire (pour les images avec transparence)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Redimensionner l'image
            resized_img = self.resize_image_keep_ratio(img)

            # Convertir en base64
            img_base64 = self.image_to_base64(resized_img)

            response = requests.post(
                'https://api.platerecognizer.com/v1/plate-reader/',
                data={'upload': img_base64},
                headers={'Authorization': f'Token {api_key}'}
            )

        if response.status_code == 200 or response.status_code == 201:
            results = response.json()

            if results['results']:
                results['results'][0]['resized_img'] = resized_img
                return results['results'][0]
        else:
            self.stdout.write(self.style.ERROR(f'Erreur de l\'API PlateRecognizer: {response.status_code}'))

        return None

    def organize_photo(self, photo_path, output_dir, image, box, vehicle_id, photo_id, date_time):
        """Organise la photo dans le dossier de sortie"""
        # Créer le dossier pour le véhicule
        vehicle_dir = os.path.join(output_dir, str(vehicle_id))
        os.makedirs(vehicle_dir, exist_ok=True)

        # Créer le nouveau nom de fichier
        new_filename = f"{vehicle_id}_{photo_id}_{date_time.strftime('%Y%m%d_%H%M%S')}.jpg"
        new_path = os.path.join(vehicle_dir, new_filename)

        # Extraire la zone à flouter
        zone_to_blur = image.crop((box['xmin'], box['ymin'], box['xmax'], box['ymax']))

        # Appliquer le flou
        blured_zone = zone_to_blur.filter(ImageFilter.GaussianBlur(radius=6))

        # Coller la zone floutée sur l'image originale
        image.paste(blured_zone, (box['xmin'], box['ymin']))

        # Sauvegarder l'image
        image.save(new_path)

        # Supprime l'image d'origine
        os.remove(photo_path)

    def update_parking_records(self, current_batch, current_vehicles):
        """Met à jour les enregistrements de stationnement"""
        # Récupérer le batch précédent
        previous_batch = Batch.objects.exclude(id=current_batch.id).first()

        if previous_batch:
            # Véhicules du batch précédent
            previous_vehicles = set(
                Photo.objects.filter(batch=previous_batch).values_list('vehicle__finger_print', flat=True)
            )

            # Nouveaux arrivants
            new_arrivals = current_vehicles - previous_vehicles
            for finger_print in new_arrivals:
                vehicle = Vehicle.objects.get(finger_print=finger_print)
                first_photo = Photo.objects.filter(vehicle=vehicle, batch=current_batch).order_by('date_time').first()
                Park.objects.create(
                    vehicle=vehicle,
                    arrival=first_photo.date_time
                )

            # Départs
            departures = previous_vehicles - current_vehicles
            for finger_print in departures:
                vehicle = Vehicle.objects.get(finger_print=finger_print)
                # Trouver le stationnement en cours
                park = Park.objects.filter(vehicle=vehicle, departure__isnull=True).first()
                if park:
                    # Utiliser la dernière photo du batch précédent comme heure de départ
                    last_photo = Photo.objects.filter(vehicle=vehicle, batch=previous_batch).order_by(
                        '-date_time').first()
                    park.departure = last_photo.date_time
                    park.save()
        else:
            # Premier batch - tous les véhicules arrivent
            for finger_print in current_vehicles:
                vehicle = Vehicle.objects.get(finger_print=finger_print)
                first_photo = Photo.objects.filter(vehicle=vehicle, batch=current_batch).order_by('date_time').first()
                Park.objects.create(
                    vehicle=vehicle,
                    arrival=first_photo.date_time
                )
