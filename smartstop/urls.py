"""
URL configuration for smartstop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from routes.journey_views import JourneyAPIView
from routes.nearby_views import ActiveStopsAPIView, NearbyStopsAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('routes.urls')),
    path('api/', include('vehicles.urls')),
    path('api/', include('metro.urls')),
    path('api/', include('board.urls')),
    path('api/journey/', JourneyAPIView.as_view(), name='journey'),
    path('api/active-stops/', ActiveStopsAPIView.as_view()),
    path('api/nearby-stops/', NearbyStopsAPIView.as_view()),
]
