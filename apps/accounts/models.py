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


class PhoneOTP(TimeStampedModel, UUIDModel):
    """
    One-time codes sent by SMS for phone verification. A citizen account is
    created with is_active=False until the REGISTRATION OTP is verified.
    """
    class Purpose(models.TextChoices):
        REGISTRATION = "registration", "Registration"
        LOGIN = "login", "Login"
        PASSWORD_RESET = "password_reset", "Password Reset"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="phone_otps")
    phone_number = models.CharField(max_length=15, db_index=True)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=Purpose.choices, db_index=True)

    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "accounts_phone_otp"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "purpose", "is_used"]),
            models.Index(fields=["phone_number", "code"]),
        ]

    def __str__(self):
        return f"OTP for {self.phone_number} ({self.get_purpose_display()})"

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def is_valid(self, code):
        return (
            not self.is_used
            and not self.is_expired
            and self.attempts < self.max_attempts
            and self.code == code
        )
