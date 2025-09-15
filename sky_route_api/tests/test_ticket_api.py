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


class TicketApiTests(APITestCase):
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
        self.order = Order.objects.create(user=self.user, flight=self.flight)
        self.ticket = Ticket.objects.create(
            order=self.order, flight=self.flight, row=1, seat=1
        )

    def test_ticket_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("sky_route_api:ticket-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["row"], 1)

    def test_ticket_list_other_user(self):
        other_user = User.objects.create_user(
            email="other@test.com", password="password123"
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.get(reverse("sky_route_api:ticket-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_ticket_retrieve(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            reverse("sky_route_api:ticket-detail", args=[self.ticket.id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["row"], 1)

    def test_ticket_retrieve_other_user(self):
        other_user = User.objects.create_user(
            email="other@test.com", password="password123"
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.get(
            reverse("sky_route_api:ticket-detail", args=[self.ticket.id])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)