from rest_framework import serializers
from .models import Vehicle, VehicleLocation


class VehicleLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleLocation
        fields = ['latitude', 'longitude', 'speed', 'updated_at']


class VehicleSerializer(serializers.ModelSerializer):
    location = VehicleLocationSerializer(read_only=True)
    route_number = serializers.CharField(source='route.number', read_only=True)
    route_name = serializers.CharField(source='route.name', read_only=True)

    class Meta:
        model = Vehicle
        fields = ['id', 'number_plate', 'route_number', 'route_name', 'is_active', 'location']


class TelemetrySerializer(serializers.Serializer):
    """Принимает GPS данные от транспорта"""
    vehicle_id = serializers.IntegerField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    speed = serializers.FloatField(default=0)