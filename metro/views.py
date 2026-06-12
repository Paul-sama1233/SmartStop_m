from rest_framework import viewsets
from .models import MetroLine, MetroStation
from .serializers import MetroLineSerializer, MetroStationSerializer


class MetroLineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MetroLine.objects.all()
    serializer_class = MetroLineSerializer


class MetroStationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MetroStation.objects.all().select_related('line')
    serializer_class = MetroStationSerializer