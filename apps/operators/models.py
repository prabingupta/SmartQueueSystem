"""
Operator-facing history: shift assignments and a log of every action an
operator takes on a token (call, skip, hold, complete, transfer, emergency).
Kept separate from Token itself so Token stays lean and this becomes the
audit trail + source data for "operator performance" analytics.
"""
from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel


class CounterAssignment(TimeStampedModel, UUIDModel):
    operator = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="counter_assignments",
        limit_choices_to={"role": "operator"},
    )
    counter = models.ForeignKey("queue_management.Counter", on_delete=models.CASCADE, related_name="assignments")

    shift_start = models.DateTimeField()
    shift_end = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "operators_counter_assignment"
        ordering = ["-shift_start"]
        indexes = [
            models.Index(fields=["operator", "is_active"]),
            models.Index(fields=["counter", "is_active"]),
        ]

    def __str__(self):
        return f"{self.operator} @ {self.counter} from {self.shift_start:%Y-%m-%d %H:%M}"


class OperatorActionLog(TimeStampedModel, UUIDModel):
    class Action(models.TextChoices):
        CALLED = "called", "Called Next"
        SKIPPED = "skipped", "Skipped"
        HELD = "held", "Put On Hold"
        RESUMED = "resumed", "Resumed From Hold"
        COMPLETED = "completed", "Completed"
        TRANSFERRED = "transferred", "Transferred"
        EMERGENCY = "emergency", "Marked Emergency"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "Marked No Show"

    operator = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="action_logs",
    )
    token = models.ForeignKey("queue_management.Token", on_delete=models.CASCADE, related_name="action_logs")
    action = models.CharField(max_length=15, choices=Action.choices, db_index=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "operators_action_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["operator", "action"]),
            models.Index(fields=["token", "action"]),
        ]

    def __str__(self):
        return f"{self.get_action_display()} — {self.token.token_number}"
