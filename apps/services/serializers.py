"""Read-only serializer for services offered per office (used during token booking)."""
from rest_framework import serializers

from .models import Service


class ServiceSerializer(serializers.ModelSerializer):
    office = serializers.SlugRelatedField(slug_field="public_id", read_only=True)

    class Meta:
        model = Service
        fields = [
            "public_id", "office", "name", "code", "description", "required_documents",
            "average_duration_minutes", "fee_amount", "requires_appointment", "is_active",
        ]
