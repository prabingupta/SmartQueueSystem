"""
Services offered per office (e.g. "New Passport Application" at a Passport
Office, "Vehicle Registration" at a Transport Office). Each service has an
average duration used by the waiting-time prediction module.
"""
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel


class Service(TimeStampedModel, UUIDModel):
    office = models.ForeignKey("offices.Office", on_delete=models.CASCADE, related_name="services")

    name = models.CharField(max_length=150)
    code = models.CharField(
        max_length=10, db_index=True,
        help_text="Short prefix used in token numbers for this service, e.g. 'PSP' -> PSP-001.",
    )
    description = models.TextField(blank=True)
    required_documents = models.TextField(
        blank=True, help_text="Free-text list of documents citizens must bring.",
    )

    average_duration_minutes = models.PositiveIntegerField(
        default=10, validators=[MinValueValidator(1)],
        help_text="Baseline service duration used for wait-time estimation until enough historical data exists.",
    )
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    requires_appointment = models.BooleanField(
        default=False, help_text="If true, walk-ins are not allowed for this service.",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "services_service"
        ordering = ["office", "name"]
        indexes = [
            models.Index(fields=["office", "is_active"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["office", "code"], name="unique_service_code_per_office"),
        ]

    def __str__(self):
        return f"{self.name} — {self.office.name}"
