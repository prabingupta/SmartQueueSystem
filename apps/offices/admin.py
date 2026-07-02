from django.contrib import admin

from .models import District, Office, OfficeCapacity


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "province")
    search_fields = ("name", "province")


class OfficeCapacityInline(admin.StackedInline):
    model = OfficeCapacity
    extra = 0


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ("name", "office_type", "district", "is_active", "max_daily_tokens")
    list_filter = ("office_type", "district", "is_active")
    search_fields = ("name", "address")
    inlines = [OfficeCapacityInline]
