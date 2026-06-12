import os
import django
import json
import math

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartstop.settings')
django.setup()

from routes.models import Stop

OSM_FILE = 'tashkent_stops.py'  # имя файла который ты скачал


def load_osm_stops():
    try:
        with open(OSM_FILE, encoding='utf-8') as f:
            data = json.load(f)
        stops = [
            s for s in data.get('elements', [])
            if 'lat' in s and 'lon' in s and s.get('tags', {}).get('name')
        ]
        print(f'Загружено {len(stops)} OSM остановок с названиями')
        return stops
    except FileNotFoundError:
        print(f'❌ Файл {OSM_FILE} не найден в корне проекта!')
        return []


def haversine_m(lat1, lng1, lat2, lng2):
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlng/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def find_nearest(lat, lng, osm_stops, max_dist_m=200):
    best, best_dist = None, max_dist_m
    for s in osm_stops:
        d = haversine_m(lat, lng, s['lat'], s['lon'])
        if d < best_dist:
            best_dist = d
            best = s
    return best, best_dist


def get_name(osm_stop):
    tags = osm_stop.get('tags', {})
    # Приоритет: узбекский → русский → любое название
    return (
        tags.get('name:uz') or
        tags.get('name:ru') or
        tags.get('name') or
        None
    )


def update_stop_names():
    osm_stops = load_osm_stops()
    if not osm_stops:
        return

    # Обновляем все остановки с автогенерированными именами
    unnamed = Stop.objects.filter(name__startswith='Остановка')
    total = unnamed.count()
    print(f'Остановок с именем "Остановка N" в БД: {total}\n')

    updated = 0
    not_found = 0

    for i, stop in enumerate(unnamed, 1):
        osm, dist = find_nearest(stop.latitude, stop.longitude, osm_stops)

        if osm:
            name = get_name(osm)
            if name:
                old_name = stop.name
                stop.name = name
                stop.save(update_fields=['name'])
                updated += 1
                if updated <= 30 or updated % 100 == 0:
                    print(f'  ✅ [{updated}] {old_name} → {name} ({dist:.0f}м)')
        else:
            not_found += 1

        # Прогресс
        if i % 500 == 0:
            print(f'  ... обработано {i}/{total}')

    print(f'\n{"="*50}')
    print(f'✅ Обновлено названий:     {updated}')
    print(f'⚠️  Не найдено в OSM:       {not_found}')
    print(f'📊 Итого обработано:        {total}')

    # Статистика оставшихся безымянных
    still_unnamed = Stop.objects.filter(name__startswith='Остановка').count()
    print(f'🔍 Осталось без названия:   {still_unnamed}')

    if still_unnamed > 0:
        print(f'\n   Для оставшихся используй stops_manual.csv')


if __name__ == '__main__':
    print('=' * 50)
    print('Обновление названий остановок из OSM данных')
    print('=' * 50)
    update_stop_names()