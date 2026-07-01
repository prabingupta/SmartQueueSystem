"""
Custom user model for the Smart Queue System.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel


class User(AbstractUser, UUIDModel, TimeStampedModel):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        OPERATOR = "operator", "Operator"
        CUSTOMER = "customer", "Customer"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        db_index=True,
    )
    phone_number = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_operator(self):
        return self.role == self.Role.OPERATOR
