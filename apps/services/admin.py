from django.contrib import admin

from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "office", "average_duration_minutes", "fee_amount", "is_active")
    list_filter = ("office", "requires_appointment", "is_active")
    search_fields = ("name", "code")
