"""
Получение реальных GPS данных транспорта Ташкента.
API: https://data.egov.uz/apiData/MainData/GetByFile?id=60fb97472a2e256d868e8253&fileType=1&tableType=2&lang=3
Запуск: python fetch_gps.py
"""
import os
import django
import requests
import json
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartstop.settings')
django.setup()

from vehicles.models import Vehicle, VehicleLocation
from routes.models import Route

GPS_URL = 'https://data.egov.uz/apiData/MainData/GetByFile?id=60fb97472a2e256d868e8253&fileType=1&tableType=2&lang=3'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://data.egov.uz',
    'Origin': 'https://data.egov.uz',
}

def fetch_gps_data():
    try:
        r = requests.get(GPS_URL, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json()
        print(f'❌ HTTP {r.status_code}: {r.text[:100]}')
        return []
    except Exception as e:
        print(f'❌ Ошибка: {e}')
        return []


def broadcast(vehicles_data):
    """Рассылаем через WebSocket"""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'vehicles',
            {'type': 'vehicles_update', 'vehicles': vehicles_data}
        )
    except Exception as e:
        print(f'  ⚠️ WebSocket: {e}')


def update_vehicles(gps_records):
    """Обновляем позиции в БД"""
    updated = 0
    # Группируем по marshrutid
    by_route = {}
    for rec in gps_records:
        mid = rec.get('marshrutid')
        if mid not in by_route:
            by_route[mid] = []
        by_route[mid].append(rec)

    vehicles_data = []

    for vehicle in Vehicle.objects.filter(is_active=True).select_related('route'):
        if not vehicle.route:
            continue

        # Ищем GPS запись по external_id маршрута
        route_external_id = str(vehicle.route.external_id)
        records = by_route.get(route_external_id, [])

        if not records:
            continue

        # Берём первую запись для этого маршрута
        rec = records[0]

        try:
            lat = float(rec['latitude'])
            lng = float(rec['longitude'])
            speed = float(rec.get('speed', 0))

            # Проверяем что координаты в Ташкенте
            if not (40.9 < lat < 41.6 and 68.9 < lng < 69.8):
                # Иногда lat/lng перепутаны
                lat, lng = lng, lat
                if not (40.9 < lat < 41.6 and 68.9 < lng < 69.8):
                    continue

            VehicleLocation.objects.update_or_create(
                vehicle=vehicle,
                defaults={
                    'latitude': lat,
                    'longitude': lng,
                    'speed': speed,
                }
            )
            updated += 1

            vehicles_data.append({
                'id': vehicle.id,
                'route_number': vehicle.route.number,
                'route_name': vehicle.route.name,
                'direction': vehicle.route.direction,
                'latitude': lat,
                'longitude': lng,
                'speed': speed,
            })

        except (ValueError, KeyError):
            continue

    return updated, vehicles_data


def run():
    print('🚌 Получение реальных GPS данных...')
    while True:
        records = fetch_gps_data()
        if records:
            updated, vehicles_data = update_vehicles(records)
            print(f'  ✅ {time.strftime("%H:%M:%S")} Обновлено: {updated} транспортных средств из {len(records)} GPS записей')
            if vehicles_data:
                broadcast(vehicles_data)
        else:
            print(f'  ⚠️ {time.strftime("%H:%M:%S")} Нет данных')

        time.sleep(15)  # обновляем каждые 15 секунд


if __name__ == '__main__':
    run()