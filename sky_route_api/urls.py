from django.urls import path, include
from rest_framework import routers

from sky_route_api.views import (RouteViewSet, AirPortViewSet,
                                 FlightViewSet, AirplaneViewSet,
                                 CrewViewSet, TicketViewSet, OrderViewSet)

app_name = 'sky_route_api'


router = routers.DefaultRouter()
router.register('routes', RouteViewSet)
router.register('airports', AirPortViewSet)
router.register('crew', CrewViewSet)
router.register('airplanes', AirplaneViewSet)
router.register('flights', FlightViewSet)
router.register("ticket", TicketViewSet)
router.register("order", OrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
