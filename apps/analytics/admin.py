from django.contrib import admin

from .models import QueueStatistic


@admin.register(QueueStatistic)
class QueueStatisticAdmin(admin.ModelAdmin):
    list_display = ("office", "service", "granularity", "date", "hour", "tokens_issued", "tokens_completed")
    list_filter = ("office", "granularity", "date")
