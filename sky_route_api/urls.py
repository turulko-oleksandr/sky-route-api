from django.urls import path, include
from rest_framework import routers

from sky_route_api.views import RouteViewSet, AirPortViewSet

app_name = 'sky_route_api'


router = routers.DefaultRouter()
router.register('routes', RouteViewSet)
router.register('airports', AirPortViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
