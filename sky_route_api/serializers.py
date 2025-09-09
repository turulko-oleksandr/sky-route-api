from rest_framework import serializers

from sky_route_api.models import Airport, Route


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
