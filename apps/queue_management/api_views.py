"""
Queue Management Engine API: token booking, live queue, and every
reception/operator action on tokens and counters.

Known simplification for this phase: operator action endpoints (complete,
hold, skip, etc.) check the IsOperator role but don't yet enforce that the
token belongs to the operator's own counter — that tightening lands
alongside full shift/assignment management in a later pass.
"""
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import (
    IsAnyStaff, IsCitizen, IsManagerOrAbove, IsOperator, IsOwnerOrStaff, IsReception,
)
from apps.queue_management import services as queue_services
from apps.queue_management.models import Counter, Token
from apps.queue_management.serializers import (
    CounterSerializer, PublicTokenSerializer, TokenBookSerializer,
    TokenSerializer, TransferSerializer, WalkInTokenSerializer,
)


class BookTokenView(APIView):
    """Citizen books a token online. Starts as BOOKED until they check in at the office."""
    permission_classes = [IsCitizen]

    def post(self, request):
        serializer = TokenBookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = queue_services.book_token(
                office=serializer.validated_data["office"],
                service=serializer.validated_data["service"],
                citizen=request.user,
                priority=serializer.validated_data["priority"],
                scheduled_time=serializer.validated_data.get("scheduled_time"),
            )
        except queue_services.QueueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TokenSerializer(token).data, status=status.HTTP_201_CREATED)


class WalkInTokenView(APIView):
    """Reception issues a token for a citizen physically at the counter — starts WAITING immediately."""
    permission_classes = [IsReception]

    def post(self, request):
        serializer = WalkInTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = queue_services.book_token(
                office=serializer.validated_data["office"],
                service=serializer.validated_data["service"],
                walk_in_name=serializer.validated_data["walk_in_name"],
                walk_in_phone=serializer.validated_data["walk_in_phone"],
                priority=serializer.validated_data["priority"],
                source=Token.Source.WALK_IN,
            )
        except queue_services.QueueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TokenSerializer(token).data, status=status.HTTP_201_CREATED)


class MyTokensView(generics.ListAPIView):
    serializer_class = TokenSerializer
    permission_classes = [IsCitizen]

    def get_queryset(self):
        return Token.objects.filter(citizen=self.request.user).select_related(
            "office", "office__district", "service",
        ).order_by("-created_at")


class TokenDetailView(generics.RetrieveAPIView):
    serializer_class = TokenSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]
    queryset = Token.objects.select_related("office", "office__district", "service", "citizen")
    lookup_field = "public_id"


class _TokenActionView(APIView):
    """Base for simple token-state-changing endpoints keyed by public_id."""
    permission_classes = [IsAuthenticated]

    def get_token(self, public_id):
        return get_object_or_404(
            Token.objects.select_related("office", "service", "citizen"), public_id=public_id,
        )

    def perform(self, token, request):
        raise NotImplementedError

    def post(self, request, public_id):
        token = self.get_token(public_id)
        try:
            token = self.perform(token, request)
        except queue_services.QueueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TokenSerializer(token).data, status=status.HTTP_200_OK)


class CancelTokenView(_TokenActionView):
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]

    def perform(self, token, request):
        self.check_object_permissions(request, token)
        return queue_services.cancel_token(token)


class CheckInTokenView(_TokenActionView):
    permission_classes = [IsAuthenticated, IsOwnerOrStaff]

    def perform(self, token, request):
        self.check_object_permissions(request, token)
        return queue_services.check_in_token(token)


class CompleteTokenView(_TokenActionView):
    permission_classes = [IsOperator]

    def perform(self, token, request):
        return queue_services.complete_token(token, operator=request.user)


class HoldTokenView(_TokenActionView):
    permission_classes = [IsOperator]

    def perform(self, token, request):
        return queue_services.hold_token(token, operator=request.user)


class ResumeTokenView(_TokenActionView):
    permission_classes = [IsAnyStaff]

    def perform(self, token, request):
        return queue_services.resume_token(token, operator=request.user)


class SkipTokenView(_TokenActionView):
    permission_classes = [IsOperator]

    def perform(self, token, request):
        return queue_services.skip_token(token, operator=request.user)


class NoShowTokenView(_TokenActionView):
    permission_classes = [IsOperator]

    def perform(self, token, request):
        return queue_services.mark_no_show(token, operator=request.user)


class EmergencyTokenView(_TokenActionView):
    """Any staff member can flag a token as an emergency priority case."""
    permission_classes = [IsAnyStaff]

    def perform(self, token, request):
        return queue_services.mark_emergency(token, operator=request.user)


class TransferTokenView(_TokenActionView):
    permission_classes = [IsOperator]

    def perform(self, token, request):
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return queue_services.transfer_token(token, serializer.validated_data["counter"], operator=request.user)


class LiveQueueView(APIView):
    """Public transparency view — no auth required, no personal data exposed."""
    permission_classes = [AllowAny]

    def get(self, request):
        office_id = request.query_params.get("office")
        service_id = request.query_params.get("service")
        if not office_id or not service_id:
            return Response(
                {"detail": "office and service query params are required."}, status=status.HTTP_400_BAD_REQUEST,
            )

        tokens = list(Token.objects.filter(
            office__public_id=office_id, service__public_id=service_id,
            queue_date=timezone.localdate(), status=Token.Status.WAITING,
        ))
        tokens.sort(key=lambda t: (queue_services.PRIORITY_WEIGHT[t.priority], t.created_at))
        return Response({
            "waiting_count": len(tokens),
            "tokens": PublicTokenSerializer(tokens, many=True).data,
        })


class CounterListView(generics.ListAPIView):
    """Manager/Admin view of counters — scoped to the manager's own office."""
    serializer_class = CounterSerializer
    permission_classes = [IsManagerOrAbove]

    def get_queryset(self):
        qs = Counter.objects.select_related("office", "current_operator").prefetch_related("services")
        if self.request.user.role != "admin":
            qs = qs.filter(office=self.request.user.office)
        return qs


class CounterClaimView(APIView):
    """An operator claims an open counter to start working it."""
    permission_classes = [IsOperator]

    def post(self, request, public_id):
        counter = get_object_or_404(Counter, public_id=public_id)
        if counter.current_operator_id and counter.current_operator_id != request.user.id:
            return Response(
                {"detail": "This counter is already staffed by another operator."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        counter.current_operator = request.user
        counter.status = Counter.Status.OPEN
        counter.save(update_fields=["current_operator", "status"])
        return Response(CounterSerializer(counter).data)


class CounterReleaseView(APIView):
    permission_classes = [IsOperator]

    def post(self, request, public_id):
        counter = get_object_or_404(Counter, public_id=public_id, current_operator=request.user)
        counter.current_operator = None
        counter.status = Counter.Status.CLOSED
        counter.save(update_fields=["current_operator", "status"])
        return Response(CounterSerializer(counter).data)


class MyCounterQueueView(APIView):
    """What the currently logged-in operator's counter can see waiting for it right now."""
    permission_classes = [IsOperator]

    def get(self, request):
        counter = Counter.objects.filter(current_operator=request.user).first()
        if not counter:
            return Response(
                {"detail": "You are not currently assigned to a counter."}, status=status.HTTP_400_BAD_REQUEST,
            )
        tokens = list(Token.objects.filter(
            office=counter.office, service__in=counter.services.all(),
            queue_date=timezone.localdate(), status=Token.Status.WAITING,
        ))
        tokens.sort(key=lambda t: (queue_services.PRIORITY_WEIGHT[t.priority], t.created_at))
        return Response({
            "counter": CounterSerializer(counter).data,
            "waiting_count": len(tokens),
            "tokens": TokenSerializer(tokens, many=True).data,
        })


class CallNextView(APIView):
    permission_classes = [IsOperator]

    def post(self, request):
        counter = Counter.objects.filter(current_operator=request.user).first()
        if not counter:
            return Response(
                {"detail": "You are not currently assigned to a counter."}, status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = queue_services.call_next_token(counter, operator=request.user)
        except queue_services.QueueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if token is None:
            return Response({"detail": "No one is waiting."}, status=status.HTTP_200_OK)
        return Response(TokenSerializer(token).data)
