import getpass
from django.core.management.base import BaseCommand
from ...models import Vehicle
from ...utils.rgpd import RGPD

class Command(BaseCommand):
    help = 'Reveal the plate of a given vehicle with the secret key and associated password'

    def add_arguments(self, parser):
        parser.add_argument('--private_key', type=str, required=True, help='Path to private key file')

    def handle(self, *args, **options):
        private_key = options['private_key']
        password = getpass.getpass(prompt='Mot de passe pour votre clé privée :').strip()

        try:
            private_key_pem = RGPD.load_private_key_from_file(private_key, password)
            for vehicle in Vehicle.objects.all():
                decoded_plate = RGPD.decrypt_text(vehicle.encoded_plate, private_key_pem, password)

                self.stdout.write(
                    self.style.SUCCESS(f'Le véhicule {vehicle.id} a pour plaque d\'immatriculation: {decoded_plate}.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur: {e}.'))


