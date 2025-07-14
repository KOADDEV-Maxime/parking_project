#!/usr/bin/env python3
"""
Script d'exemple d'utilisation du système de suivi de stationnement
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parking_project.settings')
django.setup()

from parking_tracker.models import Vehicle, Batch, Photo, Park
from django.utils import timezone
from datetime import timedelta


def create_sample_data():
    """Crée des données d'exemple pour tester le système"""
    print("🔧 Création de données d'exemple...")

    # Créer des véhicules
    vehicles = [
        Vehicle.objects.get_or_create(plate="AB-123-CD")[0],
        Vehicle.objects.get_or_create(plate="EF-456-GH")[0],
        Vehicle.objects.get_or_create(plate="IJ-789-KL")[0],
    ]

    # Créer des batches
    batch1 = Batch.objects.create()
    batch2 = Batch.objects.create()

    # Créer des photos et des stationnements
    now = timezone.now()

    # Véhicule 1 - Stationnement en cours depuis 5 jours
    arrival1 = now - timedelta(days=5)
    Photo.objects.create(
        vehicle=vehicles[0],
        batch=batch1,
        date_time=arrival1,
        latitude=48.8566,
        longitude=2.3522
    )
    Park.objects.create(
        vehicle=vehicles[0],
        arrival=arrival1
    )

    # Véhicule 2 - Stationnement terminé (8 jours)
    arrival2 = now - timedelta(days=15)
    departure2 = now - timedelta(days=7)
    Photo.objects.create(
        vehicle=vehicles[1],
        batch=batch1,
        date_time=arrival2,
        latitude=48.8566,
        longitude=2.3522
    )
    Park.objects.create(
        vehicle=vehicles[1],
        arrival=arrival2,
        departure=departure2
    )

    # Véhicule 3 - Stationnement très long (12 jours)
    arrival3 = now - timedelta(days=12)
    Photo.objects.create(
        vehicle=vehicles[2],
        batch=batch2,
        date_time=arrival3,
        latitude=48.8566,
        longitude=2.3522
    )
    Park.objects.create(
        vehicle=vehicles[2],
        arrival=arrival3
    )

    print("✅ Données d'exemple créées avec succès!")
    print(f"   - {len(vehicles)} véhicules")
    print(f"   - {Photo.objects.count()} photos")
    print(f"   - {Park.objects.count()} stationnements")


if __name__ == "__main__":
    create_sample_data()