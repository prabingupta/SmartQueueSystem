"""Serializers for token booking, the live queue, and counter management."""
from rest_framework import serializers

from apps.offices.models import Office
from apps.offices.serializers import OfficeSerializer
from apps.queue_management import services as queue_services
from apps.queue_management.models import Counter, Token
from apps.services.models import Service
from apps.services.serializers import ServiceSerializer


class TokenSerializer(serializers.ModelSerializer):
    """Full detail — for the token's owner or staff. Never exposed publicly."""
    office = OfficeSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    queue_position = serializers.SerializerMethodField()
    estimated_wait_minutes = serializers.SerializerMethodField()
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = Token
        fields = [
            "public_id", "token_number", "office", "service", "display_name",
            "status", "status_display", "source", "priority", "priority_display",
            "queue_date", "scheduled_time", "checked_in_at", "called_at",
            "serving_started_at", "completed_at", "cancelled_at",
            "queue_position", "estimated_wait_minutes", "created_at",
        ]

    def get_queue_position(self, obj):
        return queue_services.get_queue_position(obj)

    def get_estimated_wait_minutes(self, obj):
        return queue_services.estimate_wait_minutes(obj)


class PublicTokenSerializer(serializers.ModelSerializer):
    """No PII — safe for the public live-queue transparency view."""
    queue_position = serializers.SerializerMethodField()

    class Meta:
        model = Token
        fields = ["token_number", "status", "priority", "queue_position"]

    def get_queue_position(self, obj):
        return queue_services.get_queue_position(obj)


class TokenBookSerializer(serializers.Serializer):
    office = serializers.SlugRelatedField(slug_field="public_id", queryset=Office.objects.filter(is_active=True))
    service = serializers.SlugRelatedField(slug_field="public_id", queryset=Service.objects.filter(is_active=True))
    priority = serializers.ChoiceField(choices=Token.Priority.choices, default=Token.Priority.NORMAL)
    scheduled_time = serializers.TimeField(required=False, allow_null=True)

    def validate(self, attrs):
        if attrs["service"].office_id != attrs["office"].id:
            raise serializers.ValidationError("This service does not belong to the selected office.")
        return attrs


class WalkInTokenSerializer(TokenBookSerializer):
    walk_in_name = serializers.CharField(max_length=150)
    walk_in_phone = serializers.CharField(max_length=15)


class CounterSerializer(serializers.ModelSerializer):
    office = serializers.SlugRelatedField(slug_field="public_id", read_only=True)
    current_operator_name = serializers.CharField(
        source="current_operator.get_full_name", read_only=True, default=None,
    )
    services = serializers.SlugRelatedField(slug_field="public_id", many=True, read_only=True)

    class Meta:
        model = Counter
        fields = [
            "public_id", "office", "counter_number", "name", "status",
            "current_operator_name", "services", "is_active",
        ]


class TransferSerializer(serializers.Serializer):
    counter = serializers.SlugRelatedField(slug_field="public_id", queryset=Counter.objects.filter(is_active=True))
