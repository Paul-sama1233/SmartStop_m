from django.contrib import admin
from .models import Route, Stop, RouteStop


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['number', 'direction', 'name', 'vehicle_count', 'work_start', 'work_end', 'is_favorite', 'is_active']
    list_filter = ['direction', 'is_favorite', 'is_active']
    search_fields = ['number', 'name']
    list_editable = ['vehicle_count', 'work_start', 'work_end', 'is_favorite']
    ordering = ['number']


@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ['name', 'latitude', 'longitude', 'is_active']
    search_fields = ['name']


@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ['route', 'stop', 'order', 'estimated_time']