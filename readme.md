# Système de Suivi de Stationnement avec Django

Ce système permet de suivre automatiquement le stationnement de véhicules à partir de photographies avec reconnaissance automatique des plaques d'immatriculation.

## Fonctionnalités

- 📸 **Traitement automatique des photos** avec reconnaissance de plaques via PlateRecognizer
- 🗂️ **Organisation automatique** des photos par véhicule
- 📊 **Suivi des stationnements** avec détection d'arrivées et départs
- 🕐 **Calcul des durées** de stationnement (totales et en heures ouvrées)
- 📱 **Interface web responsive** avec Tailwind CSS et DaisyUI
- 🔍 **Extraction des métadonnées EXIF** (date, heure, coordonnées GPS)
- 🔑 **Chiffrement et sécurisation** des plaques d'immatriculation

## Installation

### Prérequis
- Python 3.8+
- Une clé API PlateRecognizer
- Django 4.2+

### Installation automatique
```bash
python scripts/setup_project.py
```

### Installation manuelle
```bash
# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Créer la base de données
python manage.py makemigrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser
```

## Utilisation

### 1. Démarrer le serveur
```bash
python manage.py runserver
```

### 2. Créer les clés de chiffrement
```bash
python manage.py make_keys \
  --password VOTRE_MOT_DE_PASSE_SECRET
```
__IMPORTANT__ 
- Les clés sont stockées dans le dossier `security`. Pour des raisons de confidentialité des données, **la clé privée doit être retirée du dossier et conservée sur un support tiers**.
- Le renouvellement des clés invalide la reconnaissance des véhicules déjà traités, faussant ainsi les statistiques.

### 3. Traiter les photos
```bash
python manage.py process_photos \
  --input-dir /chemin/vers/photos/entrée \
  --output-dir /chemin/vers/photos/sortie \
  --api-key VOTRE_CLE_API_PLATERECOGNIZER
```

### 4. Accéder à l'interface
- Tableau de bord: http://127.0.0.1:8000/
- Administration: http://127.0.0.1:8000/admin/

### 5. Révélation d'une plaque d'immatriculation
```bash
python manage.py reveal \
  --vehicle ID_DE_VEHICULE \
  --private_key /chemin/vers/clé/privée \
  --password VOTRE_MOT_DE_PASSE_SECRET
```

### 6. Révélation de toutes les plaques d'immatriculation
```bash
python manage.py reveal_all \
  --private_key /chemin/vers/clé/privée \
  --password VOTRE_MOT_DE_PASSE_SECRET
```

## Structure du projet

```
parking_project/
├── parking_tracker/          # Application Django principale
│   ├── models.py            # Modèles de données
│   ├── views.py             # Vues web
│   ├── admin.py             # Interface d'administration
│   └── management/commands/  # Commandes personnalisées
│       └── make_keys.py
│       └── process_photos.py
│       └── reveal.py
│       └── reveal_all.py
├── templates/               # Templates HTML
├── static/                  # Fichiers statiques
├── security/                # Stockage de la clé publique
├── media/                   # Fichiers média
│   └── photos/
│       ├── input/          # Photos à traiter
│       └── output/         # Photos classées
└── scripts/                # Scripts utilitaires
```

## Modèles de données

### Vehicle
- `plate_encoded` : Numéro de plaque, chiffré à l'aide d'une clé RSA
- `finger_print`: Empreinte de la plaque, dépendante des clés RSA
- `created`: Date de création

### Batch
- `created`: Date d'exécution du traitement

### Photo
- `vehicle`: Véhicule associé
- `batch`: Lot de traitement
- `date_time`: Date/heure de la photo
- `latitude/longitude`: Coordonnés GPS de la prise de vue
- `created`: Date de création

### Park
- `vehicle`: Véhicule
- `arrival`: Date d'arrivée
- `departure`: Date de départ (optionnel)

## Fonctionnalités avancées

### Calcul des durées ouvrées
Le système calcule automatiquement les durées de stationnement pendant les heures ouvrées (9h00-18h00, lundi-samedi).

### Alertes visuelles
- 🔵 Stationnements de 2-6 jours (fond bleu)
- 🟡 Stationnements de 7-10 jours (fond jaune)
- 🔴 Stationnements de 11+ jours (fond rouge)
- ✅ Stationnements en cours (badge vert)

### Extraction des métadonnées
- Date/heure depuis les données EXIF
- Coordonnées GPS si disponibles
- Fallback vers la date de modification du fichier

## Déploiement

### Avec Docker
```bash
docker-compose up -d
```

### Configuration de production
- Modifier `DEBUG = False` dans settings.py
- Configurer une base de données PostgreSQL
- Définir une `SECRET_KEY` sécurisée
- Configurer le serveur web (nginx/Apache)
- Créer un couple de clés RSA protégées par mot de passe (voir `manage.py make_keys`)

## API PlateRecognizer

Le système utilise l'API PlateRecognizer pour la reconnaissance automatique des plaques d'immatriculation. Vous devez :

1. Créer un compte sur https://platerecognizer.com/
2. Obtenir une clé API
3. Utiliser cette clé avec la commande `process_photos`

## Dépannage

### Problèmes courants

1. **Erreur d'importation PIL**
   ```bash
   pip install Pillow
   ```

2. **Problème de timezone**
   - Vérifiez `TIME_ZONE = 'Europe/Paris'` dans settings.py

3. **Erreur API PlateRecognizer**
   - Vérifiez votre clé API
   - Contrôlez vos quotas d'utilisation

## Contribution

Les contributions sont bienvenues ! Merci de :
1. Créer une branche du projet (fork)
2. Engager vos changements (commit)
3. Pousser vers la branche (push)
4. Ouvrir une demande de fusion (pull request)

## Licence

Ce projet est sous licence MIT.

## Suggestion d'améliorations 

- Ajout d'une notion de zones pour classer les véhicules par zone de stationnement (rue, parking...) 
- Afficher les N dernières images du véhicule sur l'interface web