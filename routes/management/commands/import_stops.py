import json
import math
from django.core.management.base import BaseCommand
from routes.models import Route, Stop, RouteStop


def haversine_m(p1, p2):
    """Расстояние в метрах между [lng,lat] точками"""
    R = 6371000
    dlat = math.radians(p2[1] - p1[1])
    dlng = math.radians(p2[0] - p1[0])
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(p1[1])) *
         math.cos(math.radians(p2[1])) *
         math.sin(dlng/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def extract_stops_from_coords(coords, interval_m=500):
    """Вычисляем позиции остановок через каждые interval_m метров"""
    stops = [coords[0]]  # первая точка — начальная остановка
    accum = 0

    for i in range(len(coords) - 1):
        d = haversine_m(coords[i], coords[i+1])
        accum += d
        if accum >= interval_m:
            stops.append(coords[i+1])
            accum = 0

    if stops[-1] != coords[-1]:
        stops.append(coords[-1])  # последняя точка — конечная остановка

    return stops


def format_stop_name(route_name, direction, order, total):
    """Генерируем название остановки"""
    parts = route_name.split('-')
    if direction == 'A-B':
        start = parts[0].strip() if parts else 'Начало'
        end = parts[-1].strip() if len(parts) > 1 else 'Конец'
    else:
        start = parts[-1].strip() if len(parts) > 1 else 'Начало'
        end = parts[0].strip() if parts else 'Конец'

    if order == 1:
        return start
    elif order == total:
        return end
    else:
        return f'Остановка {order}'


class Command(BaseCommand):
    help = 'Импорт остановок из GeoJSON маршрутов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=500,
            help='Интервал между остановками в метрах (по умолчанию 500)'
        )
        parser.add_argument(
            '--file',
            type=str,
            default='pub_transport_routes_from_passport.geojson',
            help='Путь к GeoJSON файлу'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        filepath = options['file']

        self.stdout.write(f'Загружаем файл: {filepath}')
        self.stdout.write(f'Интервал остановок: {interval}м\n')

        try:
            with open(filepath, encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Файл не найден: {filepath}'))
            return

        RouteStop.objects.all().delete()
        Stop.objects.all().delete()

        total_stops = 0
        total_routes = 0
        stop_cache = {}

        for feature in data['features']:
            props = feature['properties']
            coords = feature['geometry']['coordinates']
            route_number = props.get('route_number', '')
            direction = props.get('route_direction', 'A-B')
            route_name = props.get('route_name', '')

            try:
                route = Route.objects.get(
                    number=route_number,
                    direction=direction,
                    is_active=True
                )
            except Route.DoesNotExist:
                continue

            stop_coords = extract_stops_from_coords(coords, interval)
            total = len(stop_coords)

            for order, coord in enumerate(stop_coords, start=1):
                lng, lat = coord[0], coord[1]
                name = format_stop_name(route_name, direction, order, total)

                stop_key = f'{round(lat, 4)}_{round(lng, 4)}'
                if stop_key in stop_cache:
                    stop = stop_cache[stop_key]
                else:
                    stop = Stop.objects.create(
                        name=name,
                        latitude=lat,
                        longitude=lng,
                    )
                    stop_cache[stop_key] = stop
                    total_stops += 1

                eta_minutes = round((order - 1) * (route.avg_trip_minutes or 30) / total) if total > 1 else 0

                RouteStop.objects.create(
                    route=route,
                    stop=stop,
                    order=order,
                    estimated_time=eta_minutes,
                )

            total_routes += 1
            self.stdout.write(f'  ✓ Маршрут {route_number} ({direction}): {total} остановок')

        self.stdout.write(self.style.SUCCESS(
            f'\nГотово! Маршрутов: {total_routes}, Остановок: {total_stops}'
        ))

    def calc_eta(stop_coords_list, avg_trip_minutes, avg_speed_kmh=25):
        if not stop_coords_list or len(stop_coords_list) < 2:
            return [0] * len(stop_coords_list)

        import math

        def dist_m(p1, p2):
            R = 6371000
            dlat = math.radians(p2[0] - p1[0])
            dlng = math.radians(p2[1] - p1[1])
            a = (math.sin(dlat / 2) ** 2 +
                 math.cos(math.radians(p1[0])) *
                 math.cos(math.radians(p2[0])) *
                 math.sin(dlng / 2) ** 2)
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distances = [0.0]
        for i in range(1, len(stop_coords_list)):
            d = dist_m(stop_coords_list[i - 1], stop_coords_list[i])
            distances.append(distances[-1] + d)

        total_dist = distances[-1]
        if total_dist == 0:
            return [0] * len(stop_coords_list)

        if avg_trip_minutes:
            return [round(d / total_dist * avg_trip_minutes) for d in distances]
        else:
            return [round((d / 1000) / avg_speed_kmh * 60) for d in distances]