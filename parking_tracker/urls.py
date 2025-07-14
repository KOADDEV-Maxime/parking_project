from django.urls import path
from . import views

app_name = 'parking_tracker'

urlpatterns = [
    path('', views.parking_dashboard, name='dashboard'),
]
