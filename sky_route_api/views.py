from datetime import datetime
from django.db.models import F, Count, ExpressionWrapper, IntegerField
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from jsonschema import ValidationError
from rest_framework import viewsets, mixins
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from accounts.permissions import IsAdminOrIfAuthenticatedReadOnly
from sky_route_api.models import (
    Airport, Route, Crew,
    Airplane, Flight, Order, Ticket
)
from sky_route_api.serializers import (
    AirPortSerializer, RouteSerializer, CrewSerializer,
    AirplaneSerializer, FlightSerializer,
    FlightDetailSerializer, OrderSerializer, AirplaneListSerializer, RouteListSerializer, FlightListSerializer,
    TicketListSerializer, TicketSerializer
)


class SmallPagePagination(PageNumberPagination):
    page_size = 10
    max_page_size = 200


class BigPagePagination(PageNumberPagination):
    page_size = 20
    max_page_size = 200


class AirPortViewSet(viewsets.ModelViewSet):
    queryset = Airport.objects.all()
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly, )
    serializer_class = AirPortSerializer
    pagination_class = BigPagePagination


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.select_related("source", "destination").all()
    serializer_class = RouteSerializer
    pagination_class = BigPagePagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):
        if self.action == "list":
            return RouteListSerializer
        return RouteSerializer

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
        Flight.objects
        .select_related("route__source", "route__destination", "airplane")
        .prefetch_related("crew")
    )
    serializer_class = FlightSerializer
    pagination_class = SmallPagePagination
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_queryset(self):
        source = self.request.query_params.get("source")
        destination = self.request.query_params.get("destination")
        arrival_before = self.request.query_params.get("arrival_before")
        queryset = self.queryset.annotate(
            tickets_available=ExpressionWrapper(
                F("airplane__rows") * F("airplane__seats_in_row") - Count("tickets"),
                output_field=IntegerField()
            )
        )

        if source:
            queryset = queryset.filter(route__source__name__icontains=source)

        if destination:
            queryset = queryset.filter(route__destination__name__icontains=destination)

        if arrival_before:
            try:
                arrival_before_dt = datetime.fromisoformat(arrival_before)
                queryset = queryset.filter(arrival_time__lt=arrival_before_dt)
            except ValueError:
                raise ValidationError(
                    "arrival_before must be in ISO format (e.g., '2025-15-09T14:00')"
                )

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer
        if self.action == "retrieve":
            return FlightDetailSerializer
        return FlightSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="source",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by source airport name (case-insensitive, partial match)",
            ),
            OpenApiParameter(
                name="destination",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filter by destination airport name (case-insensitive, partial match)",
            ),
            OpenApiParameter(
                name="arrival_before",
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                description="Filter flights arriving before a specific datetime (ISO format: YYYY-MM-DDTHH:MM)",
            ),
        ],
        responses={
            200: FlightListSerializer,
            201: FlightSerializer,
            400: {"detail": "arrival_before must be in ISO format (e.g., '2025-15-09T14:00')"},
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class TicketViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = (Ticket.objects
                .select_related("flight__route", "order", "flight__airplane")
                .prefetch_related("flight__crew")
                .all())
    pagination_class = SmallPagePagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset.filter(order__user=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return TicketListSerializer
        return TicketSerializer


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    GenericViewSet,
):
    queryset = Order.objects.prefetch_related("tickets__flight")
    serializer_class = OrderSerializer
    pagination_class = BigPagePagination
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
