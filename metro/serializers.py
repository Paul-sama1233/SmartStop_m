from rest_framework import serializers
from .models import MetroLine, MetroStation


class MetroStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetroStation
        fields = ['id', 'name', 'latitude', 'longitude', 'order', 'interval_minutes']


class MetroLineSerializer(serializers.ModelSerializer):
    stations = MetroStationSerializer(many=True, read_only=True)

    class Meta:
        model = MetroLine
        fields = ['id', 'name', 'color', 'stations']