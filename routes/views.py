from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Route, Stop
from .serializers import RouteSerializer, RouteDetailSerializer, StopSerializer


class RouteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Route.objects.filter(is_active=True)
    serializer_class = RouteSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['number', 'direction', 'transport_type']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RouteDetailSerializer
        return RouteSerializer

    @action(detail=False, methods=['get'], url_path='by-number/(?P<number>[^/.]+)')
    def by_number(self, request, number=None):
        routes = Route.objects.filter(number=number, is_active=True)
        serializer = RouteDetailSerializer(routes, many=True)
        return Response(serializer.data)


class StopViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Stop.objects.filter(is_active=True)
    serializer_class = StopSerializer