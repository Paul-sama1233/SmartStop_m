"""
Django management command — импорт остановок с координатами из файла.

Формат строки:
  N. Название остановки | широта | долгота

Запуск:
  python manage.py import_stops_from_file --file routes_stops/route_stops.txt
"""
import re
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from routes.models import Route, Stop, RouteStop


class Command(BaseCommand):
    help = 'Импорт остановок с координатами из текстового файла'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='routes_stops/route_stops.txt',
            help='Путь к файлу'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить старые остановки маршрутов из файла перед импортом'
        )

    def handle(self, *args, **options):
        filepath = options['file']
        do_clear = options['clear']

        self.stdout.write('=' * 60)
        self.stdout.write('Импорт остановок с координатами')
        self.stdout.write('=' * 60)

        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f'Файл не найден: {filepath}'))
            return

        routes_data = self.parse_file(filepath)
        if not routes_data:
            return

        total_stops = 0
        total_routes = 0

        for (number, direction), stops in routes_data.items():
            count = self.import_route_stops(number, direction, stops, do_clear)
            if count > 0:
                total_stops += count
                total_routes += 1

        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS(
            f'Готово! Маршрутов: {total_routes}, Остановок: {total_stops}'
        ))

    def parse_file(self, filepath):
        routes = {}
        current_key = None

        with open(filepath, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Заголовок: ROUTE:95:A-B
                if line.startswith('ROUTE:'):
                    parts = line.split(':')
                    if len(parts) >= 3:
                        number = parts[1].strip()
                        direction = parts[2].strip()
                        current_key = (number, direction)
                        routes[current_key] = []
                    continue

                if not current_key:
                    continue

                # Парсим строку: "1. Название | lat | lng"
                # или "1. Название" (без координат)
                match = re.match(r'^\d+[.)]\s*(.+)$', line)
                if not match:
                    continue

                rest = match.group(1).strip()
                parts = [p.strip() for p in rest.split('|')]

                name = parts[0].strip()
                lat = None
                lng = None

                if len(parts) >= 3:
                    try:
                        # Убираем запятые в конце числа
                        lat = float(parts[1].replace(',', '').strip())
                        lng = float(parts[2].replace(',', '').strip())

                        # Проверяем что координаты в Ташкенте
                        if not (40.9 < lat < 41.6 and 68.9 < lng < 69.9):
                            self.stdout.write(
                                self.style.WARNING(f'  ⚠️  Подозрительные координаты: {name} — {lat}, {lng}')
                            )
                            lat, lng = None, None
                    except ValueError:
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠️  Ошибка координат: {name}')
                        )

                routes[current_key].append({
                    'name': name,
                    'lat': lat,
                    'lng': lng,
                })

        self.stdout.write(f'Загружено маршрутов: {len(routes)}')
        for key, stops in routes.items():
            with_coords = sum(1 for s in stops if s['lat'])
            self.stdout.write(f'  {key[0]} ({key[1]}): {len(stops)} остановок, {with_coords} с координатами')

        return routes

    @transaction.atomic
    def import_route_stops(self, number, direction, stops_data, do_clear):
        try:
            route = Route.objects.get(number=number, direction=direction)
        except Route.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f'\n⚠️  Маршрут {number} ({direction}) не найден в БД')
            )
            return 0

        self.stdout.write(f'\n📍 Маршрут {number} ({direction}): {len(stops_data)} остановок')

        # Очищаем старые остановки этого маршрута
        if do_clear:
            old = RouteStop.objects.filter(route=route)
            old_count = old.count()
            # Удаляем только Stop которые больше ни к чему не привязаны
            stop_ids = list(old.values_list('stop_id', flat=True))
            old.delete()
            for sid in stop_ids:
                if not RouteStop.objects.filter(stop_id=sid).exists():
                    Stop.objects.filter(id=sid).delete()
            self.stdout.write(f'  Удалено старых: {old_count}')

        # Считаем ETA пропорционально расстоянию
        import math

        def dist_m(lat1, lng1, lat2, lng2):
            R = 6371000
            dlat = math.radians(lat2 - lat1)
            dlng = math.radians(lng2 - lng1)
            a = (math.sin(dlat/2)**2 +
                 math.cos(math.radians(lat1)) *
                 math.cos(math.radians(lat2)) *
                 math.sin(dlng/2)**2)
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        # Считаем накопленное расстояние
        cum_dist = [0.0]
        for i in range(1, len(stops_data)):
            s1 = stops_data[i-1]
            s2 = stops_data[i]
            if s1['lat'] and s2['lat']:
                d = dist_m(s1['lat'], s1['lng'], s2['lat'], s2['lng'])
            else:
                d = 500  # дефолт если нет координат
            cum_dist.append(cum_dist[-1] + d)

        total_dist = cum_dist[-1]
        avg_minutes = route.avg_trip_minutes or 30

        created = 0
        for i, stop_data in enumerate(stops_data):
            # ETA пропорционально расстоянию
            eta = round(cum_dist[i] / total_dist * avg_minutes) if total_dist > 0 else 0

            # Ищем существующую остановку по координатам (радиус 30м)
            stop = None
            if stop_data['lat']:
                for existing in Stop.objects.all():
                    if existing.latitude and existing.longitude:
                        d = dist_m(
                            stop_data['lat'], stop_data['lng'],
                            existing.latitude, existing.longitude
                        )
                        if d < 30:
                            stop = existing
                            # Обновляем название если нужно
                            if existing.name != stop_data['name']:
                                existing.name = stop_data['name']
                                existing.save(update_fields=['name'])
                            break

            if not stop:
                stop = Stop.objects.create(
                    name=stop_data['name'],
                    latitude=stop_data['lat'] or 0,
                    longitude=stop_data['lng'] or 0,
                )

            # Создаём или обновляем RouteStop
            rs, created_new = RouteStop.objects.update_or_create(
                route=route,
                order=i + 1,
                defaults={
                    'stop': stop,
                    'estimated_time': eta,
                }
            )
            if created_new:
                created += 1

            self.stdout.write(
                f'  [{i+1:2}] {stop_data["name"][:40]} '
                f'({stop_data["lat"]}, {stop_data["lng"]}) '
                f'ETA: {eta}мин'
            )

        self.stdout.write(self.style.SUCCESS(f'  ✅ Создано: {created}'))
        return len(stops_data)