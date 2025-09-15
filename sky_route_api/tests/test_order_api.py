from jsonschema import ValidationError
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
    Flight,
    Order,
    Ticket,
)


class OrderApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@test.com", password="password123"
        )
        self.source = Airport.objects.create(name="A1", closest_big_city="City A")
        self.destination = Airport.objects.create(name="A2", closest_big_city="City B")
        self.route = Route.objects.create(source=self.source, destination=self.destination, distance=100)
        self.airplane_type = AirplaneType.objects.create(name="Test Type")
        self.airplane = Airplane.objects.create(name="Test Plane", rows=2, seats_in_row=2, airplane_type=self.airplane_type)
        self.flight = Flight.objects.create(
            route=self.route,
            airplane=self.airplane,
            departure_time=datetime.now(),
            arrival_time=datetime.now() + timedelta(hours=1),
        )

    def test_order_create_success(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "flight": self.flight.id,
            "tickets": [{"row": 1, "seat": 1}, {"row": 1, "seat": 2}],
        }
        response = self.client.post(reverse("sky_route_api:order-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Ticket.objects.count(), 2)

    def test_order_create_invalid_ticket(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "flight": self.flight.id,
            "tickets": [{"row": 1, "seat": 1}, {"row": 10, "seat": 10}],
        }
        response = self.client.post(
            reverse("sky_route_api:order-list"), data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tickets[1]", response.data.keys())
        self.assertIn("Row must be in range", response.data["tickets[1]"][0])

    def test_order_list_for_user(self):
        self.client.force_authenticate(user=self.user)
        Order.objects.create(user=self.user, flight=self.flight)
        response = self.client.get(reverse("sky_route_api:order-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)