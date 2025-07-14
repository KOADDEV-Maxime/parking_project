from django.core.management.base import BaseCommand
from ...models import Vehicle
from ...utils.rgpd import RGPD

class Command(BaseCommand):
    help = 'Reveal the plate of a given vehicle with the secret key and associated password'

    def add_arguments(self, parser):
        parser.add_argument('--private_key', type=str, required=True, help='Path to private key file')
        parser.add_argument('--password', type=str, required=True, help='Secret private key password')
        parser.add_argument('--vehicle', type=str, required=True, help='Vehicle idea')

    def handle(self, *args, **options):
        private_key = options['private_key']
        password = options['password']
        vehicle_id = options['vehicle']

        try:
            private_key_pem = RGPD.load_private_key_from_file(private_key, password)
            vehicle = Vehicle.objects.get(pk=vehicle_id)
            decoded_plate = RGPD.decrypt_text(vehicle.encoded_plate, private_key_pem, password)

            self.stdout.write(self.style.SUCCESS(f'Le véhicule {vehicle_id} a pour plaque d\'immatriculation: {decoded_plate}.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur: {e}.'))


