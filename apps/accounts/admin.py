from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import PhoneOTP, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "get_full_name", "role", "office", "phone_number", "is_active_staff")
    list_filter = ("role", "office", "district", "is_active_staff")
    search_fields = ("username", "first_name", "last_name", "phone_number", "national_id", "email")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Smart Queue Profile", {
            "fields": ("role", "phone_number", "phone_verified", "email_verified", "national_id",
                       "date_of_birth", "profile_photo", "address", "office", "district",
                       "is_active_staff", "preferred_language"),
        }),
    )


@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "purpose", "is_used", "attempts", "expires_at", "created_at")
    list_filter = ("purpose", "is_used")
    search_fields = ("phone_number", "user__username")
    readonly_fields = ("code",)
