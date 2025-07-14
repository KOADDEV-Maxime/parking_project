from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
import base64


class RGPD:
    """
    Une classe pour les opérations de chiffrement et déchiffrement RSA
    """

    @staticmethod
    def generate_key_pair(key_size=2048, password=None):
        """
        Génère une paire de clés RSA (publique et privée)

        Args:
            key_size (int): Taille de la clé en bits (défaut: 2048)
            password (str): Mot de passe pour protéger la clé privée (optionnel)

        Returns:
            tuple: (public_key_pem, private_key_pem)
        """
        # Génération de la clé privée
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )

        # Extraction de la clé publique
        public_key = private_key.public_key()

        # Sérialisation de la clé privée
        encryption_algorithm = serialization.NoEncryption()
        if password:
            encryption_algorithm = serialization.BestAvailableEncryption(password.encode())

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption_algorithm
        )

        # Sérialisation de la clé publique
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return public_key_pem, private_key_pem

    @staticmethod
    def encrypt_text(text, public_key_pem):
        """
        Chiffre un texte avec une clé publique RSA

        Args:
            text (str): Le texte à chiffrer
            public_key_pem (bytes): La clé publique au format PEM

        Returns:
            str: Le texte chiffré encodé en base64
        """
        # Chargement de la clé publique
        public_key = serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )

        # Chiffrement du texte
        encrypted_text = public_key.encrypt(
            text.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # Encodage en base64 pour faciliter la manipulation
        return base64.b64encode(encrypted_text).decode('utf-8')

    @staticmethod
    def decrypt_text(encrypted_text_b64, private_key_pem, password=None):
        """
        Déchiffre un texte avec une clé privée RSA

        Args:
            encrypted_text_b64 (str): Le texte chiffré encodé en base64
            private_key_pem (bytes): La clé privée au format PEM
            password (str): Le mot de passe de la clé privée (optionnel)

        Returns:
            str: Le texte déchiffré
        """
        # Décodage du base64
        encrypted_text = base64.b64decode(encrypted_text_b64.encode('utf-8'))

        # Chargement de la clé privée
        key_password = password.encode() if password else None
        private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=key_password,
            backend=default_backend()
        )

        # Déchiffrement du texte
        decrypted_text = private_key.decrypt(
            encrypted_text,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return decrypted_text.decode('utf-8')

    @staticmethod
    def load_key_from_file(file_path, password=None):
        """
        Charge une clé depuis un fichier PEM avec validation du format RSA

        Args:
            file_path (str): Chemin vers le fichier de clé
            password (str): Mot de passe si la clé est protégée

        Returns:
            bytes: Le contenu de la clé au format PEM

        Raises:
            ValueError: Si le fichier ne contient pas une clé RSA valide au format PEM
            FileNotFoundError: Si le fichier n'existe pas
        """
        try:
            with open(file_path, 'rb') as f:
                key_data = f.read()

            # Vérification du format PEM
            if not key_data.startswith(b'-----BEGIN'):
                raise ValueError("Le fichier ne contient pas une clé au format PEM")

            # Tentative de chargement pour valider la clé
            key_password = password.encode() if password else None

            # Détermine si c'est une clé privée ou publique en fonction du contenu
            if b'PRIVATE KEY' in key_data:
                # Validation de la clé privée RSA
                try:
                    private_key = serialization.load_pem_private_key(
                        key_data,
                        password=key_password,
                        backend=default_backend()
                    )
                    # Vérification que c'est bien une clé RSA
                    if not isinstance(private_key, rsa.RSAPrivateKey):
                        raise ValueError("La clé privée chargée n'est pas une clé RSA")
                except Exception as e:
                    raise ValueError(f"Impossible de charger la clé privée RSA : {str(e)}")

            elif b'PUBLIC KEY' in key_data:
                # Validation de la clé publique RSA
                try:
                    public_key = serialization.load_pem_public_key(
                        key_data,
                        backend=default_backend()
                    )
                    # Vérification que c'est bien une clé RSA
                    if not isinstance(public_key, rsa.RSAPublicKey):
                        raise ValueError("La clé publique chargée n'est pas une clé RSA")
                except Exception as e:
                    raise ValueError(f"Impossible de charger la clé publique RSA : {str(e)}")

            else:
                raise ValueError("Le fichier ne contient ni clé privée ni clé publique RSA au format PEM")

            return key_data

        except FileNotFoundError:
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Erreur lors du chargement de la clé : {str(e)}")


    @staticmethod
    def save_key_to_file(key_pem, file_path):
        """
        Sauvegarde une clé dans un fichier PEM

        Args:
            key_pem (bytes): La clé au format PEM
            file_path (str): Chemin où sauvegarder la clé
        """
        with open(file_path, 'wb') as f:
            f.write(key_pem)

    @staticmethod
    def load_public_key_from_file(file_path):
        """
        Charge une clé publique depuis un fichier PEM

        Args:
            file_path (str): Chemin vers le fichier de clé publique

        Returns:
            bytes: Le contenu de la clé publique au format PEM
        """
        return RGPD.load_key_from_file(file_path)

    @staticmethod
    def load_private_key_from_file(file_path, password=None):
        """
        Charge une clé privée depuis un fichier PEM

        Args:
            file_path (str): Chemin vers le fichier de clé privée
            password (str): Mot de passe si la clé est protégée

        Returns:
            bytes: Le contenu de la clé privée au format PEM
        """
        return RGPD.load_key_from_file(file_path, password)


    @staticmethod
    def generate_fingerprint(text, public_key_pem):
        """
        Génère une empreinte déterministe basée sur le texte et la clé publique

        Args:
            text (str): Le texte pour lequel générer l'empreinte
            public_key_pem (bytes): La clé publique au format PEM

        Returns:
            str: L'empreinte encodée en base64 (constante pour un texte donné)
        """
        # Chargement de la clé publique
        public_key = serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )

        # Génération de l'empreinte de la clé publique
        key_fingerprint = hashes.Hash(hashes.SHA256(), backend=default_backend())
        key_fingerprint.update(public_key_pem)
        key_hash = key_fingerprint.finalize()

        # Génération du hash du texte
        text_hash = hashes.Hash(hashes.SHA256(), backend=default_backend())
        text_hash.update(text.encode('utf-8'))
        text_digest = text_hash.finalize()

        # Combinaison des deux hash pour créer une empreinte unique
        combined_hash = hashes.Hash(hashes.SHA256(), backend=default_backend())
        combined_hash.update(key_hash)
        combined_hash.update(text_digest)
        combined_digest = combined_hash.finalize()

        # Encodage en base64 pour obtenir une empreinte lisible
        return base64.b64encode(combined_digest).decode('utf-8')

# Exemple d'utilisation
if __name__ == "__main__":
    # Génération des clés
    print("Génération des clés RSA...")
    public_key, private_key = RGPD.generate_key_pair(password="monmotdepasse")

    # Texte à chiffrer
    message = "Bonjour, ceci est un message secret !"
    print(f"Message original: {message}")

    # Chiffrement
    encrypted_message = RGPD.encrypt_text(message, public_key)
    print(f"Message chiffré: {encrypted_message}")

    # Déchiffrement
    decrypted_message = RGPD.decrypt_text(encrypted_message, private_key, "monmotdepasse")
    print(f"Message déchiffré: {decrypted_message}")

    # Test de l'empreinte déterministe
    test_text = "Ceci est un exemple"
    fingerprint1 = Crypto.generate_fingerprint(test_text, public_key)
    fingerprint2 = Crypto.generate_fingerprint(test_text, public_key)
    print(f"\nTest d'empreinte pour '{test_text}':")
    print(f"Empreinte 1: {fingerprint1}")
    print(f"Empreinte 2: {fingerprint2}")
    print(f"Identiques: {fingerprint1 == fingerprint2}")

    # Sauvegarde des clés (optionnel)
    # RGPD.save_key_to_file(public_key, "public_key.pem")
    # RGPD.save_key_to_file(private_key, "private_key.pem")

    # Chargement des clés depuis des fichiers (optionnel)
    # loaded_public_key = RGPD.load_public_key_from_file("public_key.pem")
    # loaded_private_key = RGPD.load_private_key_from_file("private_key.pem", "monmotdepasse")