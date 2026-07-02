"""
Pre-aggregated statistics, computed by scheduled Celery tasks (Analytics
Dashboard phase) rather than calculated live from Token on every dashboard
load. One row per office+service+date(+hour for hourly granularity).
"""
from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel


class QueueStatistic(TimeStampedModel, UUIDModel):
    class Granularity(models.TextChoices):
        HOURLY = "hourly", "Hourly"
        DAILY = "daily", "Daily"

    office = models.ForeignKey("offices.Office", on_delete=models.CASCADE, related_name="statistics")
    service = models.ForeignKey(
        "services.Service", on_delete=models.CASCADE, null=True, blank=True, related_name="statistics",
        help_text="Null means this row aggregates the whole office, not one service.",
    )

    granularity = models.CharField(max_length=10, choices=Granularity.choices, db_index=True)
    date = models.DateField(db_index=True)
    hour = models.PositiveSmallIntegerField(null=True, blank=True, help_text="0-23, only set when granularity=hourly.")

    tokens_issued = models.PositiveIntegerField(default=0)
    tokens_completed = models.PositiveIntegerField(default=0)
    tokens_cancelled = models.PositiveIntegerField(default=0)
    tokens_no_show = models.PositiveIntegerField(default=0)

    average_wait_minutes = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    average_service_minutes = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    max_queue_length = models.PositiveIntegerField(default=0)

    average_satisfaction_score = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True,
        help_text="1.00-5.00, from post-service citizen feedback.",
    )

    class Meta:
        db_table = "analytics_queue_statistic"
        ordering = ["-date", "hour"]
        constraints = [
            models.UniqueConstraint(
                fields=["office", "service", "granularity", "date", "hour"],
                name="unique_statistic_row",
            ),
        ]
        indexes = [
            models.Index(fields=["office", "granularity", "date"]),
        ]

    def __str__(self):
        scope = f"{self.office.name}" + (f" / {self.service.name}" if self.service else "")
        when = f"{self.date}" + (f" {self.hour:02d}:00" if self.hour is not None else "")
        return f"{scope} — {when}"
