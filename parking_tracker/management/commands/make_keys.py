import os
from django.core.management.base import BaseCommand
from django.conf import settings
from ...utils.rgpd import RGPD

class Command(BaseCommand):
    help = 'Create encryption keys to conform to GDPR'

    def add_arguments(self, parser):
        parser.add_argument('--password', type=str, required=True, help='Secret private key password')

    def handle(self, *args, **options):
        password = options['password']

        if os.path.exists(settings.SECURITY_PRIVATE_KEY_URL) or os.path.exists(settings.SECURITY_PUBLIC_KEY_URL):
            self.stdout.write(self.style.ERROR(f'Des clés de chiffrement existent déjà dans {settings.SECURITY_URL}.'))
            self.stdout.write(self.style.ERROR(f'Veuillez les conserver si des photos ont déjà été traitées au risque sinon d\'atteindre à l\'intégrité des données actuelles.'))
            quit()

        try:
            public_key_pem, private_key_pem = RGPD.generate_key_pair(password=password)

            RGPD.save_key_to_file(public_key_pem, settings.SECURITY_PUBLIC_KEY_URL)
            RGPD.save_key_to_file(private_key_pem, settings.SECURITY_PRIVATE_KEY_URL)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur: {e}.'))
            quit()

        self.stdout.write(self.style.SUCCESS(f'Clés crées avec succès. Veuillez déplacer la clé privée dans un endroit sûr (ex. support amovible), elle sera nécessaire si les plaques doivent être révélées.'))





