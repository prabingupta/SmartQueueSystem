"""
Custom User model with the full role hierarchy for the Smart Queue system.

Roles (from broadest public access to narrowest system control):
    CITIZEN          - books tokens, tracks queue status
    RECEPTION        - issues walk-in tokens, manages front-desk queue
    OPERATOR         - staffs a counter, calls/serves tokens
    MANAGER          - runs a single office (counters, staff, stats)
    DISTRICT_ADMIN   - oversees all offices within a district
    SUPERVISOR       - government-level oversight across districts
    ADMIN            - full system administrator
"""
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel


class User(AbstractUser, TimeStampedModel, UUIDModel):
    class Role(models.TextChoices):
        CITIZEN = "citizen", "Citizen"
        RECEPTION = "reception", "Reception Staff"
        OPERATOR = "operator", "Counter Operator"
        MANAGER = "manager", "Office Manager"
        DISTRICT_ADMIN = "district_admin", "District Administrator"
        SUPERVISOR = "supervisor", "Government Supervisor"
        ADMIN = "admin", "System Administrator"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CITIZEN, db_index=True)

    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True, db_index=True)
    phone_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    national_id = models.CharField(
        max_length=30, unique=True, null=True, blank=True,
        help_text="Citizenship number or national ID, used to prevent duplicate bookings.",
    )
    date_of_birth = models.DateField(null=True, blank=True)
    profile_photo = models.ImageField(upload_to="profile_photos/", null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)

    office = models.ForeignKey(
        "offices.Office", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="staff_members",
    )
    district = models.ForeignKey(
        "offices.District", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="district_admins",
    )

    is_active_staff = models.BooleanField(
        default=True,
        help_text="Toggle to suspend a staff account without deleting it (e.g. on leave).",
    )
    preferred_language = models.CharField(
        max_length=5, choices=[("en", "English"), ("ne", "Nepali")], default="en",
    )

    class Meta:
        db_table = "accounts_user"
        indexes = [
            models.Index(fields=["role", "office"]),
            models.Index(fields=["role", "district"]),
        ]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_staff_role(self):
        return self.role in {
            self.Role.RECEPTION, self.Role.OPERATOR, self.Role.MANAGER,
            self.Role.DISTRICT_ADMIN, self.Role.SUPERVISOR, self.Role.ADMIN,
        }
