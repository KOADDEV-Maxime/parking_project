from django.db import models
from django.utils import timezone


class Vehicle(models.Model):
    finger_print = models.TextField(unique=True, blank=True, null=True)
    encoded_plate = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.id)

class Batch(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Batch {self.id} - {self.created.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        ordering = ['-created']


class Photo(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vehicle.id} - {self.date_time.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        ordering = ['-date_time']


class Park(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    arrival = models.DateTimeField()
    departure = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.vehicle.id} - {self.arrival.strftime('%Y-%m-%d %H:%M:%S')}"

    @property
    def duration_days(self):
        end_time = self.departure or timezone.now()
        return (end_time - self.arrival).days + 1

    @property
    def business_hours_duration(self):
        """Calcule la durée en heures et minutes entre 8h30 et 18h30, lundi à samedi"""
        from datetime import time, timedelta

        start = self.arrival
        end = self.departure or timezone.now()

        total_minutes = 0
        current = start.replace(hour=0, minute=0, second=0, microsecond=0)

        while current.date() <= end.date():
            # Vérifier si c'est un jour ouvrable (lundi=0, dimanche=6)
            if current.weekday() < 6:  # Lundi à samedi
                day_start = current.replace(hour=9, minute=0)
                day_end = current.replace(hour=18, minute=00)

                # Calculer l'intersection avec la période de stationnement
                period_start = max(start, day_start)
                period_end = min(end, day_end)

                if period_start < period_end:
                    duration = period_end - period_start
                    total_minutes += duration.total_seconds() / 60

            current += timedelta(days=1)

        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        return f"{hours}h {minutes:02d}m"

    @property
    def status_class(self):
        """Retourne la classe CSS pour le statut"""
        days = self.duration_days
        if days >= 11:
            return "bg-red-100"
        elif days >= 7:
            return "bg-yellow-100"
        elif days >= 2:
            return "bg-blue-100"
        else:
            return ""

    class Meta:
        ordering = ['-arrival']
