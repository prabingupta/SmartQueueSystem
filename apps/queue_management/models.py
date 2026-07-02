"""
Core queue engine: Counter (a physical service window/desk) and Token (a
citizen's place in line). This is the busiest-write part of the whole
system, so indexes are chosen around the actual access patterns:
  - "give me today's WAITING tokens for office X, service Y, in order"
  - "what's the next token for counter Z"
  - "has citizen W already booked today" (duplicate prevention)
"""
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel


class Counter(TimeStampedModel, UUIDModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
        ON_BREAK = "on_break", "On Break"

    office = models.ForeignKey("offices.Office", on_delete=models.CASCADE, related_name="counters")
    services = models.ManyToManyField(
        "services.Service", related_name="counters", blank=True,
        help_text="Services this counter is capable of handling.",
    )
    counter_number = models.PositiveIntegerField()
    name = models.CharField(max_length=100, blank=True)

    current_operator = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="assigned_counters",
        limit_choices_to={"role": "operator"},
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.CLOSED, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "queue_counter"
        ordering = ["office", "counter_number"]
        constraints = [
            models.UniqueConstraint(fields=["office", "counter_number"], name="unique_counter_number_per_office"),
        ]
        indexes = [
            models.Index(fields=["office", "status"]),
        ]

    def __str__(self):
        return f"Counter {self.counter_number} — {self.office.name}"


class Token(TimeStampedModel, UUIDModel):
    class Status(models.TextChoices):
        BOOKED = "booked", "Booked"
        WAITING = "waiting", "Waiting"
        CALLED = "called", "Called"
        SERVING = "serving", "Serving"
        ON_HOLD = "on_hold", "On Hold"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No Show"
        TRANSFERRED = "transferred", "Transferred"

    class Source(models.TextChoices):
        ONLINE = "online", "Online Booking"
        WALK_IN = "walk_in", "Walk-in"

    class Priority(models.TextChoices):
        NORMAL = "normal", "Normal"
        PRIORITY = "priority", "Priority (Senior Citizen / PWD)"
        EMERGENCY = "emergency", "Emergency"

    office = models.ForeignKey("offices.Office", on_delete=models.PROTECT, related_name="tokens")
    service = models.ForeignKey("services.Service", on_delete=models.PROTECT, related_name="tokens")
    citizen = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="tokens",
        limit_choices_to={"role": "citizen"},
    )
    counter = models.ForeignKey(
        Counter, on_delete=models.SET_NULL, null=True, blank=True, related_name="tokens",
    )

    walk_in_name = models.CharField(max_length=150, blank=True)
    walk_in_phone = models.CharField(max_length=15, blank=True)

    token_number = models.CharField(
        max_length=20, db_index=True,
        help_text="Human-readable token, e.g. PSP-014. Unique per office per day.",
    )
    queue_date = models.DateField(db_index=True, help_text="The day this token is valid for.")
    scheduled_time = models.TimeField(null=True, blank=True, help_text="Booked slot, for online bookings.")

    status = models.CharField(max_length=15, choices=Status.choices, default=Status.BOOKED, db_index=True)
    source = models.CharField(max_length=10, choices=Source.choices, default=Source.ONLINE)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL, db_index=True)

    checked_in_at = models.DateTimeField(null=True, blank=True)
    called_at = models.DateTimeField(null=True, blank=True)
    serving_started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    estimated_wait_minutes = models.PositiveIntegerField(null=True, blank=True)
    prediction_confidence = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True,
        help_text="0.0-100.0 confidence score from the wait-time prediction model.",
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "queue_token"
        ordering = ["queue_date", "created_at"]
        constraints = [
            models.UniqueConstraint(fields=["office", "queue_date", "token_number"], name="unique_token_per_office_per_day"),
        ]
        indexes = [
            models.Index(fields=["office", "queue_date", "status"]),
            models.Index(fields=["service", "queue_date", "status"]),
            models.Index(fields=["counter", "status"]),
            models.Index(fields=["citizen", "queue_date"]),
            models.Index(fields=["priority", "status"]),
        ]

    def __str__(self):
        return f"{self.token_number} ({self.get_status_display()})"

    @property
    def display_name(self):
        return self.citizen.get_full_name() if self.citizen else self.walk_in_name
