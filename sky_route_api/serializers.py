from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from sky_route_api.models import (
    Airport, Route, Flight,
    Airplane, Crew, AirplaneType,
    Ticket, Order
)


class AirPortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ["id", "name", "closest_big_city"]


class RouteSerializer(serializers.ModelSerializer):
    source = serializers.PrimaryKeyRelatedField(queryset=Airport.objects.all())
    destination = serializers.PrimaryKeyRelatedField(queryset=Airport.objects.all())

    class Meta:
        model = Route
        fields = ["id", "source", "destination", "distance"]


class RouteListSerializer(serializers.ModelSerializer):
    source = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name",
    )
    destination = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name",
    )

    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ["id", "first_name", "last_name", "full_name"]


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ["id", "name"]


class AirplaneSerializer(serializers.ModelSerializer):
    airplane_type = serializers.PrimaryKeyRelatedField(queryset=AirplaneType.objects.all())

    class Meta:
        model = Airplane
        fields = ["id", "name", "rows", "seats_in_row", "airplane_type", "capacity"]
        read_only_fields = ["capacity"]


class AirplaneListSerializer(serializers.ModelSerializer):
    airplane_type = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name",
    )

    class Meta:
        model = Airplane
        fields = ("id", "name", "rows", "seats_in_row", "airplane_type", "capacity")


class FlightSerializer(serializers.ModelSerializer):
    route = serializers.PrimaryKeyRelatedField(queryset=Route.objects.all())
    airplane = serializers.PrimaryKeyRelatedField(queryset=Airplane.objects.all())
    crew = serializers.PrimaryKeyRelatedField(queryset=Crew.objects.all(), many=True)

    class Meta:
        model = Flight
        fields = [
            "id", "route", "airplane",
            "departure_time", "arrival_time", "crew", "flight_time"
        ]
        read_only_fields = ["flight_time"]


class TakenSeatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["row", "seat"]


class RouteDetailSerializer(RouteListSerializer):
    class Meta:
        model = Route
        fields = ("source", "destination")


class AirPortDetailSerializer(AirplaneListSerializer):
    class Meta:
        model = Airplane
        fields = ("name", "rows", "seats_in_row", "airplane_type", "capacity")


class FlightListSerializer(serializers.ModelSerializer):
    route = RouteDetailSerializer(
        read_only=True,
        many=False,
    )
    airplane = AirPortDetailSerializer(
        read_only=True,
        many=False,
    )
    crew = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field="full_name",
    )
    tickets_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "flight_time", "crew",
            "tickets_available",
        )


class FlightDetailSerializer(FlightListSerializer):
    route = RouteListSerializer(
        read_only=True,
        many=False,
    )
    airplane = AirplaneSerializer(
        read_only=True,
        many=False,
    )


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat")


class TicketListSerializer(serializers.ModelSerializer):
    flight = FlightListSerializer(read_only=True, many=False)
    customer = serializers.CharField(
        read_only=True,
        source="order.user",
    )

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight", "customer")


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(
        many=True,
        read_only=False,
        allow_null=True,
    )

    class Meta:
        model = Order
        fields = ("id", "created_at", "tickets", "flight")

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets", [])
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(
                    order=order,
                    flight=order.flight,
                    **ticket_data
                )
        return order

    def update(self, instance, validated_data):
        tickets_data = validated_data.pop("tickets", [])
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            instance.tickets.all().delete()
            for ticket_data in tickets_data:
                Ticket.objects.create(
                    order=instance,
                    flight=instance.flight,
                    **ticket_data
                )
        return instance
