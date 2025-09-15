from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from accounts.models import User
from sky_route_api.models import Crew


class CrewApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@test.com", password="password123"
        )
        self.user = User.objects.create_user(
            email="user@test.com", password="password123"
        )
        self.crew_data = {"first_name": "Test", "last_name": "Crew"}

    def test_crew_list(self):
        Crew.objects.create(**self.crew_data)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("sky_route_api:crew-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_crew_create_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            reverse("sky_route_api:crew-list"), self.crew_data
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Crew.objects.count(), 1)

    def test_crew_create_regular_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("sky_route_api:crew-list"), self.crew_data
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)