from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from accounts.models import User
from sky_route_api.models import Airport, Route


class RouteApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@test.com", password="password123"
        )
        self.user = User.objects.create_user(
            email="user@test.com", password="password123"
        )
        self.source = Airport.objects.create(name="A1", closest_big_city="City A")
        self.destination = Airport.objects.create(name="A2", closest_big_city="City B")
        self.route_data = {
            "source": self.source.id,
            "destination": self.destination.id,
            "distance": 100,
        }

    def test_route_list(self):
        self.client.force_authenticate(user=self.user)
        Route.objects.create(
            source=self.source, destination=self.destination, distance=100
        )
        response = self.client.get(reverse("sky_route_api:route-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_route_create_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("sky_route_api:route-list"), self.route_data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Route.objects.count(), 1)

    def test_route_create_regular_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("sky_route_api:route-list"), self.route_data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)