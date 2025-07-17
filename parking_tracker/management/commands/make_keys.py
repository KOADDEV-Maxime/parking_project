import getpass
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from ...utils.rgpd import RGPD


class Command(BaseCommand):
    help = 'Create encryption keys to conform to GDPR'

    def handle(self, *args, **options):
        password = getpass.getpass(prompt='Choisissez un mot de passe pour votre clé privée :').strip()
        verify = getpass.getpass(prompt='Retapez votre mot de passe, pour confirmation :').strip()

        if len(password) < 10:
            self.stdout.write(self.style.ERROR(f'Veuillez choisir un mot de passe d\'au moins 10 symboles.'))
            quit()

        if password != verify:
            self.stdout.write(self.style.ERROR(f'Les deux saisies ne correspondent pas.'))
            quit()

        if os.path.exists(settings.SECURITY_PRIVATE_KEY_URL) or os.path.exists(settings.SECURITY_PUBLIC_KEY_URL):
            self.stdout.write(self.style.ERROR(f'Des clés de chiffrement existent déjà dans {settings.SECURITY_URL}.'))
            self.stdout.write(self.style.ERROR(
                f'Veuillez les conserver si des données ont déjà été traitées au risque sinon d\'atteindre à l\'intégrité des données actuelles.'))
            quit()

        try:
            public_key_pem, private_key_pem = RGPD.generate_key_pair(password=password)
            RGPD.save_key_to_file(public_key_pem, settings.SECURITY_PUBLIC_KEY_URL)
            RGPD.save_key_to_file(private_key_pem, settings.SECURITY_PRIVATE_KEY_URL)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur: {e}.'))
            quit()

        self.stdout.write(self.style.SUCCESS(
            f'Clés crées avec succès. Veuillez déplacer la clé privée dans un endroit sûr (ex. support amovible), elle sera nécessaire si les plaques doivent être révélées.'))
