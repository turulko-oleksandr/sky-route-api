from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from sky_route_api.models import Airport, Route, AirplaneType, Airplane, Crew, Flight, Order, Ticket
from datetime import timedelta


class Command(BaseCommand):
    help = "Seed database with demo data"

    def handle(self, *args, **kwargs):
        # Create demo user
        user, _ = User.objects.get_or_create(
            email="demo@example.com"
        )
        user.set_password("demo12345")
        user.save()
        # Airports
        kyiv, _ = Airport.objects.get_or_create(name="Kyiv Boryspil", closest_big_city="Kyiv")
        lviv, _ = Airport.objects.get_or_create(name="Lviv Danylo Halytskyi", closest_big_city="Lviv")

        # Route
        route, _ = Route.objects.get_or_create(source=kyiv, destination=lviv, distance=540)

        # Airplane type
        boeing_type, _ = AirplaneType.objects.get_or_create(name="Boeing 737")

        # Airplane
        airplane, _ = Airplane.objects.get_or_create(name="Boeing-737-800", rows=30, seats_in_row=6, airplane_type=boeing_type)

        # Crew
        pilot, _ = Crew.objects.get_or_create(first_name="Ivan", last_name="Petrenko")
        copilot, _ = Crew.objects.get_or_create(first_name="Olena", last_name="Shevchenko")

        # Flight
        departure = timezone.now() + timedelta(days=1)
        arrival = departure + timedelta(hours=1)
        flight, _ = Flight.objects.get_or_create(route=route, airplane=airplane, departure_time=departure, arrival_time=arrival)
        flight.crew.add(pilot, copilot)

        # Order
        order, _ = Order.objects.get_or_create(user=user)

        # Ticket
        Ticket.objects.get_or_create(row=1, seat=1, flight=flight, order=order)

        self.stdout.write(self.style.SUCCESS("Database seeded successfully"))
