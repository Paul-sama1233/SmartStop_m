"""
GPS симулятор — движение строго по координатам маршрута из БД.
Запуск: python simulate_gps.py
"""
import os
import django
import math
import random
import time
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartstop.settings')
django.setup()

from vehicles.models import Vehicle

BASE_URL = "http://127.0.0.1:8000/api"
STEP_SECONDS = 3
SUBSTEPS = 20


def interpolate(p1, p2, t):
    return (
        p1[0] + (p2[0] - p1[0]) * t,
        p1[1] + (p2[1] - p1[1]) * t,
    )


def haversine_kmh(p1, p2, dt_seconds):
    R = 6371
    dlat = math.radians(p2[0] - p1[0])
    dlng = math.radians(p2[1] - p1[1])
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(p1[0])) *
         math.cos(math.radians(p2[0])) *
         math.sin(dlng/2)**2)
    dist_km = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    # Полное время прохождения сегмента = STEP_SECONDS * SUBSTEPS
    full_segment_time = dt_seconds * SUBSTEPS
    speed = (dist_km / (full_segment_time / 3600))
    return round(min(speed, 80.0), 1)


def send_telemetry(vehicle_id, lat, lng, speed):
    try:
        r = requests.post(f'{BASE_URL}/vehicles/telemetry/', json={
            'vehicle_id': vehicle_id,
            'latitude': round(lat, 7),
            'longitude': round(lng, 7),
            'speed': min(80, max(5, speed + random.uniform(-2, 2))),
        }, timeout=3)
        return r.status_code == 200
    except Exception as e:
        print(f'    ❌ {e}')
        return False


def load_vehicles():
    """Загружаем транспорт и координаты маршрутов прямо из БД"""
    result = {}
    vehicles = Vehicle.objects.filter(is_active=True).select_related('route')

    for v in vehicles:
        if not v.route or not v.route.coordinates or len(v.route.coordinates) < 2:
            print(f'  ⚠️  Vehicle {v.id}: нет маршрута или координат — пропускаем')
            continue

        # GeoJSON координаты: [lng, lat] → конвертируем в (lat, lng)
        coords = [(c[1], c[0]) for c in v.route.coordinates]

        # Случайная стартовая позиция
        start = random.randint(0, len(coords) - 2)

        result[v.id] = {
            'name': f'{v.route.number} ({v.route.direction})',
            'coords': coords,
            'segment': 0,
            't': 0.0,
            'total': len(coords),
        }
        print(f'  ✅ Vehicle {v.id}: маршрут {v.route.number} ({v.route.direction}) — {len(coords)} точек')

    return result


def simulate():
    print('🚌 GPS Симулятор запущен (реальные маршруты из БД)!\n')
    sim = load_vehicles()

    if not sim:
        print('❌ Нет данных для симуляции!')
        return

    print(f'\n🚀 Симулируем {len(sim)} транспортных средств\n')

    dt = STEP_SECONDS / SUBSTEPS  # секунд на один шаг

    while True:
        print(f'─── {time.strftime("%H:%M:%S")} ───')
        for vid, d in sim.items():
            coords = d['coords']
            seg = d['segment']
            t = d['t']

            p1 = coords[seg]
            p2 = coords[min(seg + 1, len(coords) - 1)]

            # Текущая позиция — интерполяция между двумя точками маршрута
            lat, lng = interpolate(p1, p2, t)
            speed = haversine_kmh(p1, p2, dt)

            ok = send_telemetry(vid, lat, lng, speed)
            icon = '✅' if ok else '❌'
            print(f'  {icon} [{vid}] {d["name"]}: ({lat:.5f}, {lng:.5f}) '
                  f'{speed:.0f} км/ч [сег {seg}/{d["total"]-2}]')

            # Двигаемся по маршруту
            d['t'] += 1.0 / SUBSTEPS
            if d['t'] >= 1.0:
                d['t'] = 0.0
                d['segment'] = seg + 1
                if d['segment'] >= len(coords) - 1:
                    d['segment'] = 0
                    print(f'    🔄 Vehicle {vid} вернулся на начало')

        print()
        time.sleep(STEP_SECONDS)


if __name__ == '__main__':
    simulate()