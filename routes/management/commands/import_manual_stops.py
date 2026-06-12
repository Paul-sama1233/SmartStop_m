import os
import django
import csv

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartstop.settings')
django.setup()

from routes.models import Route, RouteStop

with open('stops_manual.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    updated = 0
    for row in reader:
        try:
            route = Route.objects.get(
                number=row['route_number'],
                direction=row['direction']
            )
            rs = RouteStop.objects.get(
                route=route,
                order=int(row['stop_order'])
            )
            rs.stop.name = row['name']
            rs.stop.save(update_fields=['name'])
            updated += 1
            print(f"  ✅ Маршрут {row['route_number']} {row['direction']}, "
                  f"ост. {row['stop_order']} → {row['name']}")
        except Exception as e:
            print(f"  ❌ {e}")

print(f"\nОбновлено {updated} остановок")