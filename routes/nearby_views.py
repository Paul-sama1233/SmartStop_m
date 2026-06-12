"""
API для остановок:
- ActiveStopsAPIView   — все остановки активных маршрутов + номера маршрутов через них
- NearbyStopsAPIView   — остановки рядом с точкой (для метро: ближайшие автобусные)

Добавь в routes/ рядом с views.py и пропиши URL в smartstop/urls.py:
  from routes.nearby_views import ActiveStopsAPIView, NearbyStopsAPIView
  path('api/active-stops/', ActiveStopsAPIView.as_view()),
  path('api/nearby-stops/', NearbyStopsAPIView.as_view()),
"""
import math
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import RouteStop


def haversine_m(lat1, lng1, lat2, lng2):
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _sort_routes(numbers):
    """Сортируем номера маршрутов: по длине, потом по значению"""
    return sorted(numbers, key=lambda x: (len(str(x)), str(x)))


def _collect_stops():
    """Собираем остановки активных маршрутов с номерами маршрутов через них"""
    rs_qs = (RouteStop.objects
             .filter(route__is_active=True)
             .select_related('route', 'stop'))

    stops_map = {}
    for rs in rs_qs:
        s = rs.stop
        if not s.latitude:
            continue
        if s.id not in stops_map:
            stops_map[s.id] = {
                'id': s.id,
                'name': s.name,
                'latitude': s.latitude,
                'longitude': s.longitude,
                '_routes': set(),
            }
        stops_map[s.id]['_routes'].add(rs.route.number)
    return stops_map


class ActiveStopsAPIView(APIView):
    """Все остановки активных маршрутов (для режима 'по остановкам' в Автобусах)"""
    def get(self, request):
        stops_map = _collect_stops()
        result = []
        for s in stops_map.values():
            result.append({
                'id': s['id'],
                'name': s['name'],
                'latitude': s['latitude'],
                'longitude': s['longitude'],
                'routes': _sort_routes(s['_routes']),
            })
        result.sort(key=lambda x: x['name'])
        return Response({'stops': result})


class NearbyStopsAPIView(APIView):
    """
    Остановки рядом с точкой.
    GET /api/nearby-stops/?lat=41.32&lng=69.28&radius=150
    """
    def get(self, request):
        try:
            lat = float(request.GET['lat'])
            lng = float(request.GET['lng'])
        except (KeyError, ValueError, TypeError):
            return Response({'error': 'Нужны параметры lat, lng'}, status=400)

        radius = float(request.GET.get('radius', 150))

        stops_map = _collect_stops()
        result = []
        for s in stops_map.values():
            d = haversine_m(lat, lng, s['latitude'], s['longitude'])
            if d <= radius:
                result.append({
                    'id': s['id'],
                    'name': s['name'],
                    'latitude': s['latitude'],
                    'longitude': s['longitude'],
                    'distance': round(d),
                    'routes': _sort_routes(s['_routes']),
                })
        result.sort(key=lambda x: x['distance'])
        return Response({'stops': result, 'radius': radius})