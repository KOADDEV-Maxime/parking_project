#!/usr/bin/env python3
"""
Script d'installation et de configuration du projet de suivi de stationnement
"""
import os
import sys
import subprocess


def run_command(command, description):
    """Execute une commande avec gestion d'erreur"""
    print(f"📋 {description}...")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} terminé")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de {description}: {e}")
        sys.exit(1)


def main():
    print("🚗 Installation du système de suivi de stationnement")
    print("=" * 50)

    # Créer l'environnement virtuel
    run_command("python -m venv venv", "Création de l'environnement virtuel")

    # Activer l'environnement virtuel et installer les dépendances
    if os.name == 'nt':  # Windows
        pip_command = "venv\\Scripts\\pip"
        python_command = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        pip_command = "venv/bin/pip"
        python_command = "venv/bin/python"

    run_command(f"{pip_command} install --upgrade pip", "Mise à jour de pip")
    run_command(f"{pip_command} install -r requirements.txt", "Installation des dépendances")

    # Créer les migrations
    run_command(f"{python_command} manage.py makemigrations", "Création des migrations")
    run_command(f"{python_command} manage.py migrate", "Application des migrations")

    # Créer le superutilisateur
    print("\n👤 Création du superutilisateur Django")
    run_command(f"{python_command} manage.py createsuperuser", "Création du superutilisateur")

    # Créer les dossiers nécessaires
    os.makedirs("media/photos/input", exist_ok=True)
    os.makedirs("media/photos/output", exist_ok=True)
    os.makedirs("static", exist_ok=True)

    print("\n🎉 Installation terminée avec succès!")
    print("\nPour démarrer le serveur de développement:")
    print(f"  {python_command} manage.py runserver")
    print("\nPour traiter des photos:")
    print(
        f"  {python_command} manage.py process_photos --input-dir media/photos/input --output-dir media/photos/output --api-key YOUR_API_KEY")
    print("\nAccès à l'administration Django:")
    print("  http://127.0.0.1:8000/admin/")
    print("\nTableau de bord:")
    print("  http://127.0.0.1:8000/")


if __name__ == "__main__":
    main()
