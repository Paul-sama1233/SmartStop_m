from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Vehicle, VehicleLocation
from .serializers import VehicleSerializer, TelemetrySerializer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_vehicles():
    """Рассылает обновлённые позиции всем WebSocket клиентам"""
    vehicles = Vehicle.objects.filter(
        is_active=True
    ).select_related('route', 'location').exclude(location=None)

    data = [
        {
            'id': v.id,
            'route_number': v.route.number if v.route else '?',
            'route_name': v.route.name if v.route else '',
            'direction': v.route.direction if v.route else None,  # ← добавь
            'latitude': v.location.latitude,
            'longitude': v.location.longitude,
            'speed': v.location.speed,
        }
        for v in vehicles
    ]

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'vehicles',
        {
            'type': 'vehicles_update',
            'vehicles': data,
        }
    )


class VehicleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Vehicle.objects.filter(is_active=True).select_related('route', 'location')
    serializer_class = VehicleSerializer

    @action(detail=False, methods=['post'], url_path='telemetry')
    def telemetry(self, request):
        serializer = TelemetrySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            vehicle = Vehicle.objects.get(id=data['vehicle_id'], is_active=True)
        except Vehicle.DoesNotExist:
            return Response({'error': 'Транспорт не найден'}, status=status.HTTP_404_NOT_FOUND)

        VehicleLocation.objects.update_or_create(
            vehicle=vehicle,
            defaults={
                'latitude': data['latitude'],
                'longitude': data['longitude'],
                'speed': data['speed'],
            }
        )

        # Рассылаем обновление всем клиентам
        try:
            broadcast_vehicles()
        except Exception:
            pass

        return Response({'status': 'ok'})

    @action(detail=False, methods=['get'], url_path='on-map')
    def on_map(self, request):
        vehicles = Vehicle.objects.filter(
            is_active=True
        ).select_related('route', 'location').exclude(location=None)

        data = [
            {
                'id': v.id,
                'route_number': v.route.number if v.route else '?',
                'route_name': v.route.name if v.route else '',
                'number_plate': v.number_plate,
                'latitude': v.location.latitude,
                'longitude': v.location.longitude,
                'speed': v.location.speed,
                'updated_at': v.location.updated_at,
            }
            for v in vehicles
        ]
        return Response(data)