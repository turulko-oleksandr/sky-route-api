import os
import uuid

from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from datetime import timedelta

from django.utils.text import slugify

from accounts.models import User


def photo_file_path(part_root: str):
    def file_path(instance, filename):
        _, extension = os.path.splitext(filename)
        filename = f"{slugify(str(instance))}-{uuid.uuid4()}{extension}"

        return os.path.join(f"uploads/{part_root}/", filename)

    return file_path


def airport_image_file_path(instance, filename):
    return photo_file_path("airports")(instance, filename)


class Airport(models.Model):
    name = models.CharField(max_length=100, unique=True)
    closest_big_city = models.CharField(max_length=100)
    image = models.ImageField(upload_to=airport_image_file_path, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.closest_big_city})"

    class Meta:
        ordering = ["name"]


class Route(models.Model):
    source = models.ForeignKey(
        Airport,
        related_name="departures",
        on_delete=models.CASCADE,
    )
    destination = models.ForeignKey(
        Airport,
        related_name="arrivals",
        on_delete=models.CASCADE,
    )
    distance = models.IntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return f"{self.source} → {self.destination} ({self.distance} km)"

    def clean(self):
        if self.source == self.destination:
            raise ValidationError("Source and destination airports must be different.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ["source__name", "destination__name"]


class AirplaneType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Crew(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name

    class Meta:
        ordering = ["first_name", "last_name"]


class Airplane(models.Model):
    name = models.CharField(max_length=100, unique=True)
    rows = models.IntegerField(validators=[MinValueValidator(1)])
    seats_in_row = models.IntegerField(validators=[MinValueValidator(1)])
    airplane_type = models.ForeignKey(AirplaneType, on_delete=models.CASCADE)

    @property
    def capacity(self) -> int:
        return self.rows * self.seats_in_row

    def __str__(self):
        return f"{self.name} ({self.airplane_type})"

    class Meta:
        ordering = ["name"]


class Flight(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    airplane = models.ForeignKey(Airplane, on_delete=models.CASCADE)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    crew = models.ManyToManyField(Crew)

    @property
    def flight_time(self) -> str:
        duration: timedelta = self.arrival_time - self.departure_time
        hours, remainder = divmod(duration.total_seconds(), 3600)
        minutes = remainder // 60
        return f"{int(hours)}h {int(minutes)}m"

    def __str__(self):
        return f"Flight {self.id} | {self.route} | {self.departure_time:%Y-%m-%d %H:%M}"

    def clean(self):
        if self.arrival_time <= self.departure_time:
            raise ValidationError("Arrival time must be after departure time.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ["-departure_time"]


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Order {self.id} by {self.user} on {self.created_at:%Y-%m-%d %H:%M}"

    class Meta:
        ordering = ["-created_at"]


class Ticket(models.Model):
    row = models.IntegerField()
    seat = models.IntegerField()
    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="tickets",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="tickets",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["row", "seat", "flight"],
                name="unique_ticket_for_flight",
            )
        ]

    @staticmethod
    def validate_ticket(row: int, seat: int, flight: Flight) -> None:
        airplane = flight.airplane
        if not (1 <= row <= airplane.rows):
            raise ValidationError(f"Row must be in range [1, {airplane.rows}]")
        if not (1 <= seat <= airplane.seats_in_row):
            raise ValidationError(f"Seat must be in range [1, {airplane.seats_in_row}]")
        if Ticket.objects.filter(flight=flight, row=row, seat=seat).exists():
            raise ValidationError("This seat is already taken.")
        if Ticket.objects.filter(flight=flight).count() >= airplane.capacity:
            raise ValidationError("This flight is full.")

    def clean(self):
        self.validate_ticket(self.row, self.seat, self.flight)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Ticket {self.row}-{self.seat} | "
            f"Flight {self.flight.id} | Order {self.order.id}"
        )
