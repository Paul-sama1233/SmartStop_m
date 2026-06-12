from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MetroLineViewSet, MetroStationViewSet

router = DefaultRouter()
router.register(r'metro/lines', MetroLineViewSet, basename='metro-line')
router.register(r'metro/stations', MetroStationViewSet, basename='metro-station')

urlpatterns = [
    path('', include(router.urls)),
]