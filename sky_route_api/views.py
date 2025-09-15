from datetime import datetime
from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated

from accounts.permissions import IsAdminOrIfAuthenticatedReadOnly
from sky_route_api.models import (
    Airport, Route, Crew,
    Airplane, Flight, Order
)
from sky_route_api.serializers import (
    AirPortSerializer, RouteSerializer, CrewSerializer,
    AirplaneSerializer, FlightSerializer,
    FlightDetailSerializer, OrderSerializer, AirplaneListSerializer
)


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
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer
    pagination_class = BigPagePagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class AirplaneViewSet(viewsets.ModelViewSet):
    queryset = Airplane.objects.all()
    serializer_class = AirplaneSerializer
    pagination_class = SmallPagePagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "list":
            return AirplaneListSerializer
        return AirplaneSerializer


class FlightViewSet(viewsets.ModelViewSet):
    queryset = (
        Flight.objects.all()
        .select_related("route", "airplane")
        .prefetch_related("crew", "tickets")
        .annotate(
            tickets_available=(
                    F("airplane__rows") * F("airplane__seats_in_row") - Count("tickets")
            )
        )
    )
    serializer_class = FlightSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().prefetch_related("tickets")
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
