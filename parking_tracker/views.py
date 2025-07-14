from django.shortcuts import render
from django.utils import timezone
from .models import Vehicle, Park


def parking_dashboard(request):
    """Vue principale du tableau de bord"""
    vehicles = Vehicle.objects.all()

    vehicle_data = []
    sum_total_parks = 0
    sum_current_parks = 0

    for vehicle in vehicles:
        parks = Park.objects.filter(vehicle=vehicle)

        # Calculer les statistiques
        total_parks = parks.count()
        sum_total_parks += total_parks
        current_parks = parks.filter(departure__isnull=True).count()
        sum_current_parks += current_parks

        vehicle_data.append({
            'vehicle': vehicle,
            'parks': parks,
            'total_parks': total_parks,
            'current_parks': current_parks,
        })

    context = {
        'vehicle_data': vehicle_data,
        'current_parks' : sum_current_parks,
        'total_parks': sum_total_parks,
        'current_time': timezone.now(),
    }

    return render(request, 'parking_tracker/dashboard.html', context)
