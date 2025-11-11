from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from accounts.models import User
from sky_route_api.models import Airplane, AirplaneType


class AirplaneApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@test.com", password="password123"
        )
        self.user = User.objects.create_user(
            email="user@test.com", password="password123"
        )
        self.airplane_type = AirplaneType.objects.create(name="Test Type")
        self.airplane_data = {
            "name": "Test Plane",
            "rows": 10,
            "seats_in_row": 5,
            "airplane_type": self.airplane_type.id,
        }

    def test_airplane_list(self):
        self.client.force_authenticate(user=self.admin)
        Airplane.objects.create(
            name="A1",
            rows=10,
            seats_in_row=5,
            airplane_type=self.airplane_type,
        )
        response = self.client.get(reverse("sky_route_api:airplane-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_airplane_create_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("sky_route_api:airplane-list"), self.airplane_data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Airplane.objects.count(), 1)

    def test_airplane_create_regular_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("sky_route_api:airplane-list"), self.airplane_data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)