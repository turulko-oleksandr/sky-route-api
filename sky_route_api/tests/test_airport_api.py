from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from accounts.models import User
from sky_route_api.models import Airport


class AirportApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@test.com", password="password123"
        )
        self.user = User.objects.create_user(
            email="user@test.com", password="password123"
        )
        self.airport_data = {"name": "Test Airport", "closest_big_city": "Test City"}

    def test_airport_list_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("sky_route_api:airport-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_airport_create_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("sky_route_api:airport-list"), self.airport_data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Airport.objects.count(), 1)

    def test_airport_create_regular_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("sky_route_api:airport-list"), self.airport_data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)