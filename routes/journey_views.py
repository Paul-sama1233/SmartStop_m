"""
API построения маршрута на общественном транспорте.
Поддерживает прямые маршруты и маршруты с одной пересадкой.

Добавь в routes/views.py (или импортируй отсюда) и пропиши URL:
  path('journey/', JourneyAPIView.as_view(), name='journey')

Запрос:
  GET /api/journey/?from_lat=41.31&from_lng=69.27&to_lat=41.37&to_lng=69.30
"""
import math
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Stop, RouteStop


def haversine_m(lat1, lng1, lat2, lng2):
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


WALK_SPEED = 5        # км/ч пешком
BUS_SPEED = 22        # км/ч средняя по городу с остановками
WALK_RADIUS = 700     # м — максимум пешком до/от остановки
TRANSFER_RADIUS = 350 # м — максимум пешком между остановками при пересадке


class JourneyAPIView(APIView):
    def get(self, request):
        try:
            fl = float(request.GET['from_lat'])
            fg = float(request.GET['from_lng'])
            tl = float(request.GET['to_lat'])
            tg = float(request.GET['to_lng'])
        except (KeyError, ValueError, TypeError):
            return Response(
                {'error': 'Нужны параметры from_lat, from_lng, to_lat, to_lng'},
                status=400
            )

        # Загружаем все остановки активных маршрутов
        rs_qs = (RouteStop.objects
                 .filter(route__is_active=True)
                 .select_related('route', 'stop'))

        stop_routes = {}   # stop_id -> [RouteStop]
        route_stops = {}   # route_id -> [RouteStop] по порядку
        stop_by_id = {}    # stop_id -> Stop

        for rs in rs_qs:
            stop_routes.setdefault(rs.stop_id, []).append(rs)
            route_stops.setdefault(rs.route_id, []).append(rs)
            stop_by_id[rs.stop_id] = rs.stop

        for rid in route_stops:
            route_stops[rid].sort(key=lambda x: x.order)

        active_stops = list(stop_by_id.values())

        # Предрасчёт ближайших остановок для пересадок
        nearby = {}
        for s in active_stops:
            if not s.latitude:
                continue
            lst = []
            for o in active_stops:
                if o.id == s.id or not o.latitude:
                    continue
                d = haversine_m(s.latitude, s.longitude, o.latitude, o.longitude)
                if d <= TRANSFER_RADIUS:
                    lst.append(o.id)
            nearby[s.id] = lst

        def near(lat, lng, radius):
            out = []
            for s in active_stops:
                if not s.latitude:
                    continue
                d = haversine_m(lat, lng, s.latitude, s.longitude)
                if d <= radius:
                    out.append((s, d))
            out.sort(key=lambda x: x[1])
            return out

        start = near(fl, fg, WALK_RADIUS)
        end = near(tl, tg, WALK_RADIUS)
        end_walk = {s.id: d for s, d in end}

        if not start or not end:
            return Response({'journeys': [], 'message': 'Рядом нет остановок'})

        def bus_leg(route, board_rs, alight_rs):
            seg = [r for r in route_stops[route.id]
                   if board_rs.order <= r.order <= alight_rs.order]
            dist = 0
            for i in range(1, len(seg)):
                a = stop_by_id[seg[i-1].stop_id]
                b = stop_by_id[seg[i].stop_id]
                if a.latitude and b.latitude:
                    dist += haversine_m(a.latitude, a.longitude, b.latitude, b.longitude)
            minutes = max(round(dist / 1000 / BUS_SPEED * 60), 1)
            return {
                'mode': 'bus',
                'route_number': route.number,
                'direction': route.direction,
                'from_stop': stop_by_id[board_rs.stop_id].name,
                'to_stop': stop_by_id[alight_rs.stop_id].name,
                'stops_count': len(seg) - 1,
                'minutes': minutes,
                'path': [
                    {'name': stop_by_id[r.stop_id].name,
                     'lat': stop_by_id[r.stop_id].latitude,
                     'lng': stop_by_id[r.stop_id].longitude}
                    for r in seg
                ],
            }

        def walk_leg(meters):
            return {
                'mode': 'walk',
                'meters': round(meters),
                'minutes': max(round(meters / 1000 / WALK_SPEED * 60), 1),
            }

        results = []

        # ---------- ПРЯМЫЕ МАРШРУТЫ ----------
        for s_stop, s_walk in start[:10]:
            for brs in stop_routes.get(s_stop.id, []):
                rid = brs.route_id
                best = None
                for ars in route_stops[rid]:
                    if ars.order > brs.order and ars.stop_id in end_walk:
                        if best is None or end_walk[ars.stop_id] < end_walk[best.stop_id]:
                            best = ars
                if best:
                    legs = [
                        walk_leg(s_walk),
                        bus_leg(brs.route, brs, best),
                        walk_leg(end_walk[best.stop_id]),
                    ]
                    results.append({
                        'type': 'direct',
                        'transfers': 0,
                        'total_minutes': sum(l['minutes'] for l in legs),
                        'legs': legs,
                    })

        # ---------- С ОДНОЙ ПЕРЕСАДКОЙ ----------
        # Ищем всегда (не только когда прямых нет), но ограничиваем
        for s_stop, s_walk in start[:6]:
            for brs in stop_routes.get(s_stop.id, []):
                r1 = brs.route_id
                seen_r2 = set()
                for trs in route_stops[r1]:
                    if trs.order <= brs.order:
                        continue
                    # точки пересадки: сама остановка + соседние
                    transfer_ids = [trs.stop_id] + nearby.get(trs.stop_id, [])
                    for t_id in transfer_ids:
                        t_stop = stop_by_id[t_id]
                        walk_transfer = haversine_m(
                            stop_by_id[trs.stop_id].latitude,
                            stop_by_id[trs.stop_id].longitude,
                            t_stop.latitude, t_stop.longitude
                        )
                        for b2 in stop_routes.get(t_id, []):
                            r2 = b2.route_id
                            if r2 == r1 or r2 in seen_r2:
                                continue
                            for ars in route_stops[r2]:
                                if ars.order > b2.order and ars.stop_id in end_walk:
                                    seen_r2.add(r2)
                                    legs = [
                                        walk_leg(s_walk),
                                        bus_leg(brs.route, brs, trs),
                                        walk_leg(walk_transfer),
                                        bus_leg(b2.route, b2, ars),
                                        walk_leg(end_walk[ars.stop_id]),
                                    ]
                                    results.append({
                                        'type': 'transfer',
                                        'transfers': 1,
                                        'total_minutes': sum(l['minutes'] for l in legs),
                                        'legs': legs,
                                    })
                                    break

        # Сортируем по времени, убираем дубли, берём топ-4
        results.sort(key=lambda x: x['total_minutes'])
        seen = set()
        uniq = []
        for r in results:
            sig = tuple(
                (l.get('route_number'), l.get('mode'))
                for l in r['legs'] if l['mode'] == 'bus'
            )
            if sig in seen:
                continue
            seen.add(sig)
            uniq.append(r)
            if len(uniq) >= 4:
                break

        return Response({'journeys': uniq})