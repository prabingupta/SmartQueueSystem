from django.contrib import admin

from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ("recipient", "channel", "event_type", "status", "sent_at")
    list_filter = ("channel", "event_type", "status")
    search_fields = ("recipient", "user__username")
