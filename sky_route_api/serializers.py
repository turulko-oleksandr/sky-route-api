from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from sky_route_api.models import (Airport, Route, Flight,
                                  Airplane, Crew, AirplaneType, Ticket)


class AirPortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = '__all__'


class RouteSerializer(serializers.ModelSerializer):
    source = AirPortSerializer()
    destination = AirPortSerializer()

    class Meta:
        model = Route
        fields = [
            'id', 'source',
            'destination', 'distance'
        ]


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ['id', 'first_name', 'last_name']


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ['name']


class AirplaneSerializer(serializers.ModelSerializer):
    airplane_type = AirplaneTypeSerializer()

    class Meta:
        model = Airplane
        fields = ['id', 'name', 'rows', 'seats_in_row', 'airplane_type']

    def create(self, validated_data):
        airplane_type_data = validated_data.pop('airplane_type')
        with transaction.atomic():
            airplane_type, _ = AirplaneType.objects.get_or_create(
                **airplane_type_data
            )
            airplane = Airplane.objects.create(
                airplane_type=airplane_type,
                **validated_data
            )
        return airplane

    def update(self, instance, validated_data):
        airplane_type_data = validated_data.pop('airplane_type', None)
        with transaction.atomic():
            if airplane_type_data:
                airplane_type, _ = AirplaneType.objects.get_or_create(**airplane_type_data)
                instance.airplane_type = airplane_type

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.save()
        return instance


class FlightSerializer(serializers.ModelSerializer):
    route = RouteSerializer()
    airplane = AirplaneSerializer()
    crew = CrewSerializer(many=True)

    class Meta:
        model = Flight
        fields = [
            'id', 'route', 'airplane',
            'departure_time', 'arrival_time',
            'crew'
        ]

    def create(self, validated_data):
        route_data = validated_data.pop('route')
        source_data = route_data.pop('source')
        destination_data = route_data.pop('destination')

        airplane_data = validated_data.pop('airplane')
        airplane_type_data = airplane_data.pop('airplane_type')

        crew_data = validated_data.pop('crew')

        with transaction.atomic():
            source, _ = Airport.objects.get_or_create(**source_data)
            destination, _ = Airport.objects.get_or_create(**destination_data)

            route, _ = Route.objects.get_or_create(
                source=source,
                destination=destination,
                defaults={'distance': route_data['distance']}
            )

            airplane_type, _ = AirplaneType.objects.get_or_create(**airplane_type_data)

            airplane, _ = Airplane.objects.get_or_create(
                airplane_type=airplane_type,
                name=airplane_data['name'],
                rows=airplane_data['rows'],
                seats_in_row=airplane_data['seats_in_row']
            )

            flight = Flight.objects.create(
                route=route,
                airplane=airplane,
                **validated_data
            )

            for member_data in crew_data:
                crew_member, _ = Crew.objects.get_or_create(**member_data)
                flight.crew.add(crew_member)

        return flight

    def update(self, instance, validated_data):
        route_data = validated_data.pop('route', None)
        airplane_data = validated_data.pop('airplane', None)
        crew_data = validated_data.pop('crew', None)

        with transaction.atomic():
            if route_data:
                source_data = route_data.pop('source', None)
                destination_data = route_data.pop('destination', None)

                if source_data:
                    source, _ = Airport.objects.get_or_create(**source_data)
                    instance.route.source = source
                if destination_data:
                    destination, _ = Airport.objects.get_or_create(**destination_data)
                    instance.route.destination = destination

                for attr, value in route_data.items():
                    setattr(instance.route, attr, value)
                instance.route.save()

            if airplane_data:
                airplane_type_data = airplane_data.pop('airplane_type', None)
                if airplane_type_data:
                    airplane_type, _ = AirplaneType.objects.get_or_create(**airplane_type_data)
                    instance.airplane.airplane_type = airplane_type
                for attr, value in airplane_data.items():
                    setattr(instance.airplane, attr, value)
                instance.airplane.save()

            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            if crew_data is not None:
                instance.crew.clear()
                for member_data in crew_data:
                    crew_member, _ = Crew.objects.get_or_create(**member_data)
                    instance.crew.add(crew_member)

        return instance


class TicketSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        flight = attrs.get("flight")
        row = attrs.get("row")
        seat = attrs.get("seat")

        if row > flight.airplane.rows:
            raise ValidationError(
                {"row": "Row is greater than flight.airplane.rows"}
            )
        if seat > flight.airplane.seats_in_row:
            raise ValidationError(
                {"seat": "Seat is greater than flight.airplane.seats_in_row"}
            )

        if Ticket.objects.filter(flight=flight, row=row, seat=seat).exists():
            raise ValidationError(
                {"seat": "This ticket already exists."}
            )

        return data

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight")


class FlightListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = ("id", "departure_time", "arrival_time", "route", "airplane")

class TakenSeatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")


class FlightDetailSerializer(serializers.ModelSerializer):
    route = RouteSerializer(many=False, read_only=True)
    airplane = AirplaneSerializer(many=False, read_only=True)
    crew = CrewSerializer(many=True, read_only=True)
    taken_seats = TakenSeatsSerializer(
        source="tickets", many=True, read_only=True
    )

    class Meta:
        model = Flight
        fields = (
            "id",
            "departure_time",
            "arrival_time",
            "route",
            "airplane",
            "crew",
            "taken_seats",
        )

