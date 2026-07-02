"""
Shared abstract base models.

Every domain model in the project (Token, Office, Service, Counter, ...)
should inherit from TimeStampedModel (and SoftDeleteModel where deletion
needs to be reversible/audited) instead of re-declaring created_at/updated_at
on every model.
"""
import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """Adds created_at / updated_at to any model that inherits it."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    """
    Adds a public-facing UUID identifier separate from the internal
    auto-increment primary key. Use `public_id` in URLs/QR codes/APIs
    instead of exposing sequential database IDs.
    """

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    class Meta:
        abstract = True


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteModel(models.Model):
    """
    Soft delete instead of hard delete, so audit trails and historical
    reports (e.g. "tokens issued last month") stay accurate even after
    a record is "removed" by a user.
    """

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        from django.utils import timezone

        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)


class BaseModel(TimeStampedModel, UUIDModel, SoftDeleteModel):
    """Convenience combination of the three mixins above."""

    class Meta:
        abstract = True


class AuditLog(TimeStampedModel, UUIDModel):
    """
    Who did what, when. Written by AuditLogMiddleware (apps.core.middleware)
    for state-changing (POST/PUT/PATCH/DELETE) requests from authenticated
    users, plus explicitly from sensitive service-layer actions (e.g.
    token cancellation, role changes) that deserve a record even if the
    HTTP-level log would miss context.
    """

    user = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs",
    )
    action = models.CharField(max_length=100, db_index=True, help_text="e.g. 'token.cancel', 'user.role_change'.")
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=64, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    method = models.CharField(max_length=10, blank=True)
    path = models.CharField(max_length=255, blank=True)

    metadata = models.JSONField(default=dict, blank=True, help_text="Extra context, e.g. before/after values.")

    class Meta:
        db_table = "core_audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "action"]),
            models.Index(fields=["model_name", "object_id"]),
        ]

    def __str__(self):
        return f"{self.user} — {self.action} @ {self.created_at:%Y-%m-%d %H:%M}"
