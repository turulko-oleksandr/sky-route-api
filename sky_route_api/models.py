from django.db import models
from rest_framework.exceptions import ValidationError

from accounts.models import User


class Airport(models.Model):
    name = models.CharField(max_length=100)
    closest_big_city = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.closest_big_city})"


class Route(models.Model):
    source = models.ForeignKey(
        Airport,
        related_name='departures',
        on_delete=models.CASCADE
    )
    destination = models.ForeignKey(
        Airport,
        related_name='arrivals',
        on_delete=models.CASCADE
    )
    distance = models.IntegerField()

    def __str__(self):
        return f"{self.source} → {self.destination} ({self.distance} km)"


class AirplaneType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Crew(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Airplane(models.Model):
    name = models.CharField(max_length=100)
    rows = models.IntegerField()
    seats_in_row = models.IntegerField()
    airplane_type = models.ForeignKey(AirplaneType, on_delete=models.CASCADE)

    @property
    def total_count_of_seats(self):
        return self.rows * self.seats_in_row

    def __str__(self):
        return f"{self.name} ({self.airplane_type})"


class Flight(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    airplane = models.ForeignKey(Airplane, on_delete=models.CASCADE)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(Crew)

    def __str__(self):
        return (f"Flight {self.id} "
                f"| {self.route} "
                f"| {self.departure_time: %Y-%m-%d %H:%M}")


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE)

    def __str__(self):
        return (f"Order {self.id} by {self.user} "
                f"on {self.created_at: %Y-%m-%d %H:%M}")


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='tickets'
    )

    class Meta:
        # Correctly defined metadata for the model
        constraints = [
            models.UniqueConstraint(
                fields=['row', 'seat', 'flight'],
                name='unique_ticket_for_flight'
            )
        ]

    @staticmethod
    def validate_seat(seat: int, row: int,
                      num_rows: int,
                      num_seats: int,
                      error_to_raise):
        if not (1 <= seat <= num_seats):
            raise error_to_raise({
                "seat": f"seat must be in the range [1, {num_seats}]"
            })
        if not (1 <= row <= num_rows):
            raise error_to_raise({
                "row": f"row must be in the range [1, {num_rows}]"
            })

    def clean(self):
        Ticket.validate_seat(
            self.seat, self.row, self.flight.airplane.rows, self.flight.airplane.seats_in_row, ValidationError
        )

    def __str__(self):
        return (f"Ticket {self.row}-{self.seat} "
                f"| Flight {self.flight.id} "
                f"| Order {self.order.id}")
