"""
Business logic for the queue engine: token booking, token-number
generation, queue position/wait estimation, and every operator action
(call next, skip, hold, resume, complete, transfer, emergency).

Kept out of views so the same logic can be reused by the API, the admin,
management commands, and Celery tasks later without duplication.
"""
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.operators.models import OperatorActionLog
from apps.queue_management.models import Counter, Token

PRIORITY_WEIGHT = {
    Token.Priority.EMERGENCY: 0,
    Token.Priority.PRIORITY: 1,
    Token.Priority.NORMAL: 2,
}


class QueueError(Exception):
    """Raised for business-rule violations (office full, wrong state transition, etc.)."""


def _log(operator, token, action, notes=""):
    if operator is not None:
        OperatorActionLog.objects.create(operator=operator, token=token, action=action, notes=notes)


def _next_token_number(office, service, queue_date):
    count = Token.objects.filter(office=office, service=service, queue_date=queue_date).count()
    return f"{service.code}-{count + 1:03d}"


def book_token(*, office, service, citizen=None, walk_in_name="", walk_in_phone="",
                queue_date=None, scheduled_time=None, source=Token.Source.ONLINE,
                priority=Token.Priority.NORMAL):
    """
    Creates a Token. ONLINE bookings start as BOOKED (citizen still needs to
    check in on arrival); WALK_IN tokens start as WAITING immediately since
    the citizen is already physically present at the office.
    """
    queue_date = queue_date or timezone.localdate()

    if not service.is_active or not office.is_active:
        raise QueueError("This service is not currently available.")

    issued_today = Token.objects.filter(office=office, queue_date=queue_date).exclude(
        status=Token.Status.CANCELLED
    ).count()
    if issued_today >= office.max_daily_tokens:
        raise QueueError("This office has reached its token limit for today. Please try again tomorrow.")

    if citizen is not None:
        already_booked = Token.objects.filter(
            citizen=citizen, service=service, queue_date=queue_date,
        ).exclude(status__in=[Token.Status.CANCELLED, Token.Status.NO_SHOW]).exists()
        if already_booked:
            raise QueueError("You already have an active token for this service today.")

    initial_status = Token.Status.WAITING if source == Token.Source.WALK_IN else Token.Status.BOOKED

    for _attempt in range(5):
        token_number = _next_token_number(office, service, queue_date)
        try:
            with transaction.atomic():
                token = Token.objects.create(
                    office=office, service=service, citizen=citizen,
                    walk_in_name=walk_in_name, walk_in_phone=walk_in_phone,
                    token_number=token_number, queue_date=queue_date,
                    scheduled_time=scheduled_time, source=source, priority=priority,
                    status=initial_status,
                )
            return token
        except IntegrityError:
            continue  # token_number collision under concurrency — retry with a fresh count
    raise QueueError("Could not generate a token number. Please try again.")


def check_in_token(token):
    """Citizen arrives at the office for an ONLINE-booked token -> becomes WAITING."""
    if token.status != Token.Status.BOOKED:
        raise QueueError("This token cannot be checked in.")
    token.status = Token.Status.WAITING
    token.checked_in_at = timezone.now()
    token.save(update_fields=["status", "checked_in_at"])
    return token


def cancel_token(token):
    if token.status in {Token.Status.COMPLETED, Token.Status.CANCELLED}:
        raise QueueError("This token can no longer be cancelled.")
    token.status = Token.Status.CANCELLED
    token.cancelled_at = timezone.now()
    token.save(update_fields=["status", "cancelled_at"])
    return token


def get_queue_position(token):
    """1-indexed position within its own office+service+day WAITING queue, or None if not waiting/called."""
    if token.status not in {Token.Status.WAITING, Token.Status.CALLED}:
        return None
    queue = list(
        Token.objects.filter(
            office=token.office, service=token.service, queue_date=token.queue_date, status=Token.Status.WAITING,
        )
    )
    queue.sort(key=lambda t: (PRIORITY_WEIGHT[t.priority], t.created_at))
    for index, t in enumerate(queue, start=1):
        if t.pk == token.pk:
            return index
    return len(queue) + 1


def estimate_wait_minutes(token):
    """
    Simple heuristic: (people ahead * average service duration) / open counters
    serving this service. Refined later by the dedicated ML-based Waiting
    Time Prediction phase — this keeps the product usable in the meantime.
    """
    position = get_queue_position(token)
    if position is None:
        return None
    open_counters = Counter.objects.filter(
        office=token.office, status=Counter.Status.OPEN, services=token.service,
    ).count()
    open_counters = max(open_counters, 1)
    ahead = max(position - 1, 0)
    return round((ahead * token.service.average_duration_minutes) / open_counters)


def call_next_token(counter, operator=None):
    if counter.status != Counter.Status.OPEN:
        raise QueueError("This counter is not open.")
    candidates = list(
        Token.objects.filter(
            office=counter.office, service__in=counter.services.all(),
            queue_date=timezone.localdate(), status=Token.Status.WAITING,
        )
    )
    if not candidates:
        return None
    candidates.sort(key=lambda t: (PRIORITY_WEIGHT[t.priority], t.created_at))
    token = candidates[0]
    token.status = Token.Status.CALLED
    token.counter = counter
    token.called_at = timezone.now()
    token.save(update_fields=["status", "counter", "called_at"])
    _log(operator, token, OperatorActionLog.Action.CALLED)
    return token


def start_serving(token, operator=None):
    if token.status != Token.Status.CALLED:
        raise QueueError("Token must be called before serving can start.")
    token.status = Token.Status.SERVING
    token.serving_started_at = timezone.now()
    token.save(update_fields=["status", "serving_started_at"])
    return token


def complete_token(token, operator=None):
    if token.status not in {Token.Status.CALLED, Token.Status.SERVING}:
        raise QueueError("Only a called or serving token can be completed.")
    token.status = Token.Status.COMPLETED
    token.completed_at = timezone.now()
    token.save(update_fields=["status", "completed_at"])
    _log(operator, token, OperatorActionLog.Action.COMPLETED)
    return token


def hold_token(token, operator=None):
    if token.status not in {Token.Status.CALLED, Token.Status.SERVING}:
        raise QueueError("Only a called or serving token can be put on hold.")
    token.status = Token.Status.ON_HOLD
    token.save(update_fields=["status"])
    _log(operator, token, OperatorActionLog.Action.HELD)
    return token


def resume_token(token, operator=None):
    if token.status != Token.Status.ON_HOLD:
        raise QueueError("This token is not on hold.")
    token.status = Token.Status.WAITING
    token.counter = None
    token.save(update_fields=["status", "counter"])
    _log(operator, token, OperatorActionLog.Action.RESUMED)
    return token


def skip_token(token, operator=None):
    if token.status != Token.Status.CALLED:
        raise QueueError("Only a called token can be skipped.")
    token.status = Token.Status.WAITING
    token.counter = None
    token.save(update_fields=["status", "counter"])
    _log(operator, token, OperatorActionLog.Action.SKIPPED)
    return token


def mark_no_show(token, operator=None):
    if token.status != Token.Status.CALLED:
        raise QueueError("Only a called token can be marked as a no-show.")
    token.status = Token.Status.NO_SHOW
    token.save(update_fields=["status"])
    _log(operator, token, OperatorActionLog.Action.NO_SHOW)
    return token


def mark_emergency(token, operator=None):
    token.priority = Token.Priority.EMERGENCY
    token.save(update_fields=["priority"])
    _log(operator, token, OperatorActionLog.Action.EMERGENCY)
    return token


def transfer_token(token, new_counter, operator=None):
    if token.status not in {Token.Status.CALLED, Token.Status.SERVING}:
        raise QueueError("Only a called or serving token can be transferred.")
    token.counter = new_counter
    token.status = Token.Status.CALLED
    token.save(update_fields=["counter", "status"])
    _log(operator, token, OperatorActionLog.Action.TRANSFERRED, notes=f"To counter {new_counter.counter_number}")
    return token
