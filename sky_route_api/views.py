from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from sky_route_api.models import Airport, Route, Crew, Airplane, Flight
from sky_route_api.serializers import (AirPortSerializer, RouteSerializer,
                                       CrewSerializer, AirplaneSerializer,
                                       FlightSerializer)


class SmallPagePagination(PageNumberPagination):
    page_size = 10
    max_page_size = 200


class BigPagePagination(PageNumberPagination):
    page_size = 20
    max_page_size = 200


class AirPortViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirPortSerializer
    pagination_class = BigPagePagination


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    pagination_class = BigPagePagination


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    pagination_class = BigPagePagination


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer
    pagination_class = SmallPagePagination


class FlightViewSet(viewsets.ModelViewSet):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer
    pagination_class = SmallPagePagination
