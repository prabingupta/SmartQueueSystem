"""
Computer-vision crowd monitoring: cameras per office, periodic snapshots
(people count, density) produced by the YOLO detection pipeline, and alerts
raised when occupancy crosses a threshold. Built in full in the AI Crowd
Monitoring phase — models come first so other apps can reference them.
"""
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel


class CameraFeed(TimeStampedModel, UUIDModel):
    class SourceType(models.TextChoices):
        WEBCAM = "webcam", "Local Webcam"
        RTSP = "rtsp", "RTSP Stream"
        UPLOAD = "upload", "Uploaded Video (testing)"

    office = models.ForeignKey("offices.Office", on_delete=models.CASCADE, related_name="cameras")
    name = models.CharField(max_length=100, help_text="e.g. 'Main Waiting Hall', 'Entrance'.")
    source_type = models.CharField(max_length=10, choices=SourceType.choices, default=SourceType.RTSP)
    stream_url = models.CharField(max_length=500, blank=True, help_text="RTSP/HTTP URL, empty for local webcam index 0.")

    is_active = models.BooleanField(default=True, db_index=True)
    detection_interval_seconds = models.PositiveIntegerField(
        default=10, validators=[MinValueValidator(1)],
        help_text="How often the YOLO pipeline pulls and analyzes a frame from this feed.",
    )

    class Meta:
        db_table = "crowd_ai_camera_feed"
        ordering = ["office", "name"]

    def __str__(self):
        return f"{self.name} — {self.office.name}"


class CrowdSnapshot(TimeStampedModel, UUIDModel):
    camera = models.ForeignKey(CameraFeed, on_delete=models.CASCADE, related_name="snapshots")
    people_count = models.PositiveIntegerField()
    occupancy_percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="people_count / office.capacity.max_capacity * 100, computed at capture time.",
    )
    captured_at = models.DateTimeField(db_index=True)
    annotated_frame = models.ImageField(
        upload_to="crowd_ai/snapshots/%Y/%m/%d/", null=True, blank=True,
        help_text="Frame with YOLO bounding boxes drawn, stored only for a rolling retention window.",
    )

    class Meta:
        db_table = "crowd_ai_snapshot"
        ordering = ["-captured_at"]
        indexes = [
            models.Index(fields=["camera", "captured_at"]),
        ]

    def __str__(self):
        return f"{self.camera.name}: {self.people_count} people @ {self.captured_at:%H:%M:%S}"


class CrowdAlert(TimeStampedModel, UUIDModel):
    class AlertType(models.TextChoices):
        OVERCROWDING = "overcrowding", "Overcrowding"
        CAMERA_OFFLINE = "camera_offline", "Camera Offline"

    class Severity(models.TextChoices):
        WARNING = "warning", "Warning"
        CRITICAL = "critical", "Critical"

    camera = models.ForeignKey(CameraFeed, on_delete=models.CASCADE, related_name="alerts")
    snapshot = models.ForeignKey(CrowdSnapshot, on_delete=models.SET_NULL, null=True, blank=True, related_name="alerts")

    alert_type = models.CharField(max_length=20, choices=AlertType.choices, db_index=True)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.WARNING)

    triggered_at = models.DateTimeField(db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="acknowledged_alerts",
    )

    class Meta:
        db_table = "crowd_ai_alert"
        ordering = ["-triggered_at"]
        indexes = [
            models.Index(fields=["camera", "resolved_at"]),
        ]

    def __str__(self):
        return f"{self.get_alert_type_display()} — {self.camera.name} @ {self.triggered_at:%H:%M}"
