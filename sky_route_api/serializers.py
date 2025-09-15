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


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ["id", "first_name", "last_name"]


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


class FlightDetailSerializer(serializers.ModelSerializer):
    route = RouteSerializer(read_only=True)
    airplane = AirplaneSerializer(read_only=True)
    crew = CrewSerializer(many=True, read_only=True)
    taken_seats = serializers.SerializerMethodField()

    class Meta:
        model = Flight
        fields = [
            "id", "departure_time", "arrival_time",
            "route", "airplane", "crew", "taken_seats"
        ]

    @staticmethod
    def get_taken_seats(obj):
        tickets = obj.tickets.all()
        return TakenSeatsSerializer(tickets, many=True).data


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["id", "row", "seat", "flight", "order"]

    def validate(self, attrs):
        ticket = Ticket(**attrs)
        try:
            ticket.full_clean()
        except ValidationError as e:
            raise ValidationError(e.message_dict)
        return attrs


class TicketForOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ["row", "seat"]


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketForOrderSerializer(many=True)

    class Meta:
        model = Order
        fields = ["id", "flight", "tickets", "created_at"]

    def create(self, validated_data):
        tickets_data = validated_data.pop("tickets", [])
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                ticket = Ticket(order=order, flight=order.flight, **ticket_data)
                ticket.full_clean()
                ticket.save()
        return order

    def update(self, instance, validated_data):
        tickets_data = validated_data.pop("tickets", [])
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            instance.tickets.all().delete()
            for ticket_data in tickets_data:
                ticket = Ticket(order=instance, flight=instance.flight, **ticket_data)
                ticket.full_clean()
                ticket.save()

        return instance
