from django.contrib import admin
from .models import Vehicle, Batch, Photo, Park


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['id', 'created']
    search_fields = ['id']
    readonly_fields = ['created']


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'created', 'photo_count']
    readonly_fields = ['created']

    def photo_count(self, obj):
        return obj.photo_set.count()

    photo_count.short_description = 'Nombre de photos'


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'batch', 'date_time', 'latitude', 'longitude', 'created']
    list_filter = ['batch', 'vehicle', 'date_time']
    search_fields = ['vehicle__id']
    readonly_fields = ['created']


@admin.register(Park)
class ParkAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'arrival', 'departure', 'duration_days', 'is_current']
    list_filter = ['arrival', 'departure', 'vehicle']
    search_fields = ['vehicle__id']

    def is_current(self, obj):
        return obj.departure is None

    is_current.boolean = True
    is_current.short_description = 'En cours'