"""
Импорт маршрутов из GeoJSON файла.
Запуск:
  python manage.py import_routes
  python manage.py import_routes --file pub_transport_routes_from_passport.geojson
"""
import json
import os
from django.core.management.base import BaseCommand
from routes.models import Route


class Command(BaseCommand):
    help = 'Импорт маршрутов из GeoJSON файла'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='pub_transport_routes_from_passport.geojson',
            help='Путь к GeoJSON файлу (по умолчанию: pub_transport_routes_from_passport.geojson)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить все маршруты перед импортом'
        )

    def handle(self, *args, **options):
        filepath = options['file']
        do_clear = options['clear']

        self.stdout.write('=' * 60)
        self.stdout.write(f'Импорт маршрутов из {filepath}')
        self.stdout.write('=' * 60)

        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f'Файл не найден: {filepath}'))
            return

        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)

        features = data.get('features', [])
        self.stdout.write(f'Найдено объектов в файле: {len(features)}')

        if do_clear:
            deleted = Route.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Удалено маршрутов: {deleted[0]}'))

        created = 0
        updated = 0
        skipped = 0

        for feature in features:
            props = feature.get('properties', {})
            geometry = feature.get('geometry', {})

            # Извлекаем поля из properties
            external_id = str(props.get('id') or props.get('route_id') or '')
            number = str(
                props.get('route_number') or
                props.get('number') or
                props.get('name') or ''
            ).strip()
            name = str(
                props.get('route_name') or
                props.get('name') or
                props.get('route_number') or ''
            ).strip()
            direction = str(
                props.get('route_direction') or
                props.get('direction') or
                'A-B'
            ).strip()
            transport_type = str(
                props.get('transport_type') or
                props.get('type') or
                'bus'
            ).strip()

            # Длина маршрута
            length_km = None
            raw_len = props.get('route_length_ab') or props.get('route_length_ba') or props.get('length')
            if raw_len:
                try:
                    length_km = float(raw_len)
                except (ValueError, TypeError):
                    pass

            # Гараж / автопарк
            garage = str(props.get('garage') or props.get('park') or '').strip() or None

            # Количество транспорта
            vehicle_count = 0
            raw_vc = props.get('vehicle_count') or props.get('buses')
            if raw_vc:
                try:
                    vehicle_count = int(raw_vc)
                except (ValueError, TypeError):
                    pass

            # Время работы
            work_start = props.get('work_start') or props.get('start_time') or None
            work_end = props.get('work_end') or props.get('end_time') or None

            # Среднее время поездки
            avg_trip_minutes = None
            raw_avg = props.get('avg_trip_minutes') or props.get('trip_time')
            if raw_avg:
                try:
                    avg_trip_minutes = int(raw_avg)
                except (ValueError, TypeError):
                    pass

            # Координаты из геометрии
            coordinates = []
            if geometry.get('type') == 'LineString':
                coordinates = geometry.get('coordinates', [])
            elif geometry.get('type') == 'MultiLineString':
                # Объединяем все линии в одну
                for line in geometry.get('coordinates', []):
                    coordinates.extend(line)

            if not number:
                skipped += 1
                continue

            # Создаём или обновляем маршрут
            obj, was_created = Route.objects.update_or_create(
                number=number,
                direction=direction,
                defaults={
                    'external_id': external_id,
                    'name': name,
                    'transport_type': transport_type,
                    'length_km': length_km,
                    'garage': garage,
                    'vehicle_count': vehicle_count,
                    'work_start': work_start,
                    'work_end': work_end,
                    'avg_trip_minutes': avg_trip_minutes,
                    'coordinates': coordinates,
                    'is_active': True,
                }
            )

            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS(f'✅ Создано:   {created}'))
        self.stdout.write(self.style.SUCCESS(f'🔄 Обновлено: {updated}'))
        self.stdout.write(self.style.WARNING(f'⏭  Пропущено: {skipped}'))
        self.stdout.write(f'Итого в БД:  {Route.objects.count()} маршрутов')