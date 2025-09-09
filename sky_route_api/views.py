from datetime import datetime
from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from accounts.permissions import IsAdminOrIfAuthenticatedReadOnly
from sky_route_api.models import Airport, Route, Crew, Airplane, Flight
from sky_route_api.serializers import (AirPortSerializer, RouteSerializer,
                                       CrewSerializer, AirplaneSerializer,
                                       FlightSerializer,
                                       FlightListSerializer, FlightDetailSerializer)


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
    queryset = (
        Flight.objects.all()
        .select_related("route", "airplane")
        .annotate(
            tickets_available=(
                F("airplane__rows") * F("airplane__seats_in_row")
                - Count("ticket")
            )
        )
    )
    serializer_class = FlightSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        departure_date = self.request.query_params.get("date")
        route_id_str = self.request.query_params.get("route")

        queryset = self.queryset

        if departure_date:
            departure_date = datetime.strptime(departure_date, "%Y-%m-%d").date()
            queryset = queryset.filter(departure_time__date=departure_date)

        if route_id_str:
            queryset = queryset.filter(route_id=int(route_id_str))

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer

        if self.action == "retrieve":
            return FlightDetailSerializer

        return FlightSerializer
