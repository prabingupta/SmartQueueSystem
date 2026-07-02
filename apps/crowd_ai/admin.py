from django.contrib import admin

from .models import CameraFeed, CrowdAlert, CrowdSnapshot


@admin.register(CameraFeed)
class CameraFeedAdmin(admin.ModelAdmin):
    list_display = ("name", "office", "source_type", "is_active", "detection_interval_seconds")
    list_filter = ("office", "source_type", "is_active")


@admin.register(CrowdSnapshot)
class CrowdSnapshotAdmin(admin.ModelAdmin):
    list_display = ("camera", "people_count", "occupancy_percentage", "captured_at")
    list_filter = ("camera__office",)
    date_hierarchy = "captured_at"


@admin.register(CrowdAlert)
class CrowdAlertAdmin(admin.ModelAdmin):
    list_display = ("camera", "alert_type", "severity", "triggered_at", "resolved_at")
    list_filter = ("alert_type", "severity", "camera__office")
