import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class VehicleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('vehicles', self.channel_name)
        await self.accept()
        # Отправляем текущие позиции сразу при подключении
        vehicles = await self.get_vehicles()
        await self.send(text_data=json.dumps({
            'type': 'vehicles_update',
            'vehicles': vehicles
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard('vehicles', self.channel_name)

    async def receive(self, text_data):
        pass

    async def vehicles_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'vehicles_update',
            'vehicles': event['vehicles']
        }))

    @database_sync_to_async
    def get_vehicles(self):
        from vehicles.models import Vehicle
        vehicles = Vehicle.objects.filter(
            is_active=True
        ).select_related('route', 'location').exclude(location=None)

        return [
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