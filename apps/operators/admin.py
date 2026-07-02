from django.contrib import admin

from .models import CounterAssignment, OperatorActionLog


@admin.register(CounterAssignment)
class CounterAssignmentAdmin(admin.ModelAdmin):
    list_display = ("operator", "counter", "shift_start", "shift_end", "is_active")
    list_filter = ("counter__office", "is_active")


@admin.register(OperatorActionLog)
class OperatorActionLogAdmin(admin.ModelAdmin):
    list_display = ("token", "operator", "action", "created_at")
    list_filter = ("action",)
    search_fields = ("token__token_number",)
