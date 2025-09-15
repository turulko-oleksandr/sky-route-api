from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from datetime import datetime, timedelta

from accounts.models import User
from sky_route_api.models import (
    Airport,
    Route,
    AirplaneType,
    Airplane,
    Crew,
    Flight,
    Ticket,
    Order,
)


class FlightApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@test.com", password="password123"
        )
        self.user = User.objects.create_user(
            email="user@test.com", password="password123"
        )
        self.source = Airport.objects.create(name="Kyiv", closest_big_city="Kyiv")
        self.destination = Airport.objects.create(name="Lviv", closest_big_city="Lviv")
        self.route = Route.objects.create(
            source=self.source, destination=self.destination, distance=500
        )
        self.airplane_type = AirplaneType.objects.create(name="Test Type")
        self.airplane = Airplane.objects.create(
            name="Test Plane",
            rows=2,
            seats_in_row=2,
            airplane_type=self.airplane_type,
        )
        self.crew = Crew.objects.create(first_name="John", last_name="Doe")

        self.flight = Flight.objects.create(
            route=self.route,
            airplane=self.airplane,
            departure_time=datetime.now(),
            arrival_time=datetime.now() + timedelta(hours=1),
        )
        self.flight.crew.add(self.crew)

    def test_flight_list_filters(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("sky_route_api:flight-list"),
            {"source": "Kyiv", "destination": "Lviv"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["route"]["source"], "Kyiv"
        )

    def test_flight_list_with_available_tickets(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("sky_route_api:flight-list"))
        self.assertEqual(response.data["results"][0]["tickets_available"], 4)

        order = Order.objects.create(user=self.user, flight=self.flight)
        Ticket.objects.create(order=order, flight=self.flight, row=1, seat=1)

        response = self.client.get(reverse("sky_route_api:flight-list"))
        self.assertEqual(response.data["results"][0]["tickets_available"], 3)

    def test_flight_create_admin(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            "route": self.route.id,
            "airplane": self.airplane.id,
            "departure_time": "2023-01-01T10:00:00Z",
            "arrival_time": "2023-01-01T12:00:00Z",
            "crew": [self.crew.id],
        }
        response = self.client.post(reverse("sky_route_api:flight-list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Flight.objects.count(), 2)

    def test_flight_create_regular_user(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "route": self.route.id,
            "airplane": self.airplane.id,
            "departure_time": "2023-01-01T10:00:00Z",
            "arrival_time": "2023-01-01T12:00:00Z",
            "crew": [self.crew.id],
        }
        response = self.client.post(reverse("sky_route_api:flight-list"), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)