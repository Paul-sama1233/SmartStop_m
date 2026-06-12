import re
import os
from django.core.management.base import BaseCommand
from routes.models import Route, RouteStop


class Command(BaseCommand):
    help = 'Импорт названий остановок из текстового файла'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='route_stops.txt',
            help='Путь к файлу с остановками (по умолчанию: route_stops.txt)'
        )

    def handle(self, *args, **options):
        filepath = options['file']

        self.stdout.write('=' * 55)
        self.stdout.write('Импорт названий остановок')
        self.stdout.write('=' * 55)

        routes_data = self.parse_file(filepath)
        if not routes_data:
            return

        total = 0
        for (number, direction), names in routes_data.items():
            updated = self.update_stops(number, direction, names)
            total += updated

            # Авто-разворот для обратного направления
            rev_dir = 'B-A' if direction == 'A-B' else 'A-B'
            if (number, rev_dir) not in routes_data:
                reversed_names = list(reversed(names))
                updated_rev = self.update_stops(number, rev_dir, reversed_names)
                total += updated_rev

        self.stdout.write('=' * 55)
        self.stdout.write(
            self.style.SUCCESS(f'Всего обновлено: {total} остановок')
        )

    def parse_file(self, filepath):
        routes = {}
        current_key = None

        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f'Файл не найден: {filepath}'))
            self.stdout.write('Положи файл в корень проекта или укажи путь через --file')
            return {}

        with open(filepath, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if line.startswith('ROUTE:'):
                    parts = line.split(':')
                    if len(parts) >= 3:
                        number = parts[1].strip()
                        direction = parts[2].strip()
                        current_key = (number, direction)
                        routes[current_key] = []
                    continue

                if current_key:
                    match = re.match(r'^\d+[.)]\s*(.+)$', line)
                    if match:
                        routes[current_key].append(match.group(1).strip())

        self.stdout.write(f'Загружено маршрутов из файла: {len(routes)}')
        return routes

    def update_stops(self, number, direction, names):
        try:
            route = Route.objects.get(number=number, direction=direction)
        except Route.DoesNotExist:
            self.stdout.write(
                self.style.WARNING(f'  Маршрут {number} ({direction}) не найден в БД')
            )
            return 0

        route_stops = RouteStop.objects.filter(route=route)\
            .select_related('stop').order_by('order')

        db_count = route_stops.count()
        names_count = len(names)

        self.stdout.write(f'\nМаршрут {number} ({direction}):')
        self.stdout.write(f'   В файле: {names_count} | В БД: {db_count}')

        updated = 0
        for i, rs in enumerate(route_stops):
            if i < names_count:
                new_name = names[i]
                if rs.stop.name != new_name:
                    rs.stop.name = new_name
                    rs.stop.save(update_fields=['name'])
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(f'   Обновлено: {updated}')
        )
        return updated