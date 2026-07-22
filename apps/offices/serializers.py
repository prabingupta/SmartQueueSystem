"""Read-only serializers for the public office directory (used during token booking)."""
from rest_framework import serializers

from .models import District, Office


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["public_id", "name", "province"]


class OfficeSerializer(serializers.ModelSerializer):
    district = DistrictSerializer(read_only=True)
    office_type_display = serializers.CharField(source="get_office_type_display", read_only=True)

    class Meta:
        model = Office
        fields = [
            "public_id", "name", "office_type", "office_type_display", "district",
            "address", "latitude", "longitude", "phone_number", "email",
            "opening_time", "closing_time", "working_days", "max_daily_tokens", "is_active",
        ]
