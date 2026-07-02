from django.contrib import admin

from .models import Counter, Token


@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ("counter_number", "office", "status", "current_operator", "is_active")
    list_filter = ("office", "status", "is_active")
    filter_horizontal = ("services",)


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ("token_number", "office", "service", "status", "priority", "queue_date", "counter")
    list_filter = ("office", "status", "priority", "source", "queue_date")
    search_fields = ("token_number", "walk_in_name", "walk_in_phone", "citizen__username")
    date_hierarchy = "queue_date"
