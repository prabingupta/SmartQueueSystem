"""
Every SMS/Email sent to a citizen is logged here — both for debugging
("did the reminder actually go out?") and for the notification history
shown in the citizen's dashboard.
"""
from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel


class NotificationLog(TimeStampedModel, UUIDModel):
    class Channel(models.TextChoices):
        SMS = "sms", "SMS"
        EMAIL = "email", "Email"

    class EventType(models.TextChoices):
        TOKEN_BOOKED = "token_booked", "Token Booked"
        REMINDER = "reminder", "Reminder"
        QUEUE_APPROACHING = "queue_approaching", "Queue Approaching"
        NOW_SERVING = "now_serving", "Now Serving"
        COUNTER_CHANGED = "counter_changed", "Counter Changed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications",
    )
    token = models.ForeignKey(
        "queue_management.Token", on_delete=models.SET_NULL, null=True, blank=True, related_name="notifications",
    )

    channel = models.CharField(max_length=10, choices=Channel.choices, db_index=True)
    event_type = models.CharField(max_length=25, choices=EventType.choices, db_index=True)
    recipient = models.CharField(max_length=150, help_text="Phone number or email address at time of sending.")
    message = models.TextField()

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "notifications_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["token", "event_type"]),
        ]

    def __str__(self):
        return f"{self.get_channel_display()} · {self.get_event_type_display()} -> {self.recipient} [{self.status}]"
