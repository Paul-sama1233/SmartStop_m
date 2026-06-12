import math
from rest_framework import serializers
from .models import Route, Stop, RouteStop


class StopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stop
        fields = ['id', 'name', 'latitude', 'longitude']


class RouteStopSerializer(serializers.ModelSerializer):
    stop = StopSerializer()

    class Meta:
        model = RouteStop
        fields = ['order', 'stop', 'estimated_time']


def haversine_m(lat1, lng1, lat2, lng2):
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlng/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


class RouteDetailSerializer(serializers.ModelSerializer):
    stops = serializers.SerializerMethodField()

    class Meta:
        model = Route
        fields = [
            'id', 'external_id', 'number', 'name',
            'transport_type', 'direction', 'length_km',
            'coordinates', 'vehicle_count', 'work_start',
            'work_end', 'avg_trip_minutes', 'bus_brand',
            'is_favorite', 'stops'
        ]

    def get_stops(self, route):
        route_stops = route.route_stops.select_related('stop').order_by('order')
        stops_list = list(route_stops)

        if not stops_list:
            return []

        # Считаем накопленное расстояние от первой остановки
        cum_dist = [0.0]
        for i in range(1, len(stops_list)):
            s1 = stops_list[i-1].stop
            s2 = stops_list[i].stop
            if s1.latitude and s2.latitude:
                d = haversine_m(s1.latitude, s1.longitude, s2.latitude, s2.longitude)
            else:
                d = 0
            cum_dist.append(cum_dist[-1] + d)

        total_dist = cum_dist[-1]

        # Масштабируем по avg_trip_minutes или считаем по 25 км/ч
        avg_minutes = route.avg_trip_minutes
        AVG_SPEED_KMH = 25

        result = []
        for i, rs in enumerate(stops_list):
            if total_dist > 0 and avg_minutes:
                # Пропорционально расстоянию от avg_trip_minutes
                eta = round(cum_dist[i] / total_dist * avg_minutes)
            elif total_dist > 0:
                # По средней скорости 25 км/ч
                eta = round((cum_dist[i] / 1000) / AVG_SPEED_KMH * 60)
            else:
                eta = rs.estimated_time

            result.append({
                'order': rs.order,
                'stop': StopSerializer(rs.stop).data,
                'estimated_time': eta,
                'distance_from_start': round(cum_dist[i] / 1000, 2),  # км
            })

        return result


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = [
            'id', 'external_id', 'number', 'name',
            'transport_type', 'direction', 'length_km',
            'coordinates', 'vehicle_count', 'work_start',
            'work_end', 'avg_trip_minutes', 'bus_brand', 'is_favorite'
        ]