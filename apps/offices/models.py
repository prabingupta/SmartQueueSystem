"""
Office structure: District -> Office. Every queue, service, and counter
belongs to an Office; every Office belongs to a District (for district-level
reporting and District Admin scoping).
"""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel


class District(TimeStampedModel, UUIDModel):
    name = models.CharField(max_length=100, unique=True)
    province = models.CharField(max_length=100)

    class Meta:
        db_table = "offices_district"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Office(TimeStampedModel, UUIDModel):
    class OfficeType(models.TextChoices):
        PASSPORT = "passport", "Passport Office"
        TRANSPORT = "transport", "Transport Management Office"
        MUNICIPALITY = "municipality", "Municipality Office"
        WARD = "ward", "Ward Office"
        INLAND_REVENUE = "inland_revenue", "Inland Revenue Office"
        LAND_REVENUE = "land_revenue", "Land Revenue Office"
        HOSPITAL = "hospital", "Hospital"
        PUBLIC_SERVICE_COMMISSION = "psc", "Public Service Commission Office"

    name = models.CharField(max_length=150)
    office_type = models.CharField(max_length=30, choices=OfficeType.choices, db_index=True)
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="offices")

    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    opening_time = models.TimeField(default="10:00")
    closing_time = models.TimeField(default="17:00")
    working_days = models.CharField(
        max_length=50, default="Sun,Mon,Tue,Wed,Thu",
        help_text="Comma-separated working days (Nepal government week: Sun-Thu, plus 1st/3rd Sat off).",
    )

    max_daily_tokens = models.PositiveIntegerField(
        default=200, validators=[MinValueValidator(1)],
        help_text="Cap on tokens issued per day, to prevent overbooking beyond office capacity.",
    )

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "offices_office"
        ordering = ["district__name", "name"]
        indexes = [
            models.Index(fields=["office_type", "district"]),
            models.Index(fields=["is_active"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["name", "district"], name="unique_office_name_per_district"),
        ]

    def __str__(self):
        return f"{self.name} ({self.district.name})"


class OfficeCapacity(TimeStampedModel, UUIDModel):
    """
    Physical capacity of an office's waiting area, used by the crowd_ai
    module to compute occupancy_percentage = current_count / max_capacity.
    Kept as a separate model (rather than a field on Office) since it may
    later need history (renovations changing capacity over time).
    """
    office = models.OneToOneField(Office, on_delete=models.CASCADE, related_name="capacity")
    max_capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5000)],
        help_text="Maximum comfortable occupancy of the waiting area.",
    )
    alert_threshold_percentage = models.PositiveIntegerField(
        default=85, validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Occupancy % at which a congestion alert is triggered.",
    )

    class Meta:
        db_table = "offices_office_capacity"

    def __str__(self):
        return f"{self.office.name} capacity: {self.max_capacity}"
