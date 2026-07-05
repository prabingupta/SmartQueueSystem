"""
OTP generation and delivery. Delivery is abstracted behind `send_otp_sms` so
swapping in a real SMS gateway later (Phase: Notifications) means changing
one function, not every call site.
"""
import random
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.accounts.models import PhoneOTP
from apps.notifications.models import NotificationLog

OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = getattr(settings, "OTP_EXPIRY_MINUTES", 10)


def generate_otp_code() -> str:
    return f"{random.randint(0, 10**OTP_LENGTH - 1):0{OTP_LENGTH}d}"


def issue_otp(user, phone_number: str, purpose: str) -> PhoneOTP:
    """
    Invalidate any previous unused OTPs of the same purpose for this user,
    create a fresh one, and dispatch it.
    """
    PhoneOTP.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)

    otp = PhoneOTP.objects.create(
        user=user,
        phone_number=phone_number,
        code=generate_otp_code(),
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )
    send_otp_sms(phone_number, otp.code, purpose)
    return otp


def send_otp_sms(phone_number: str, code: str, purpose: str) -> None:
    """
    Sends the OTP via SMS gateway if configured; otherwise logs it so
    development/testing can proceed without a real gateway. Every attempt
    (real or simulated) is recorded in NotificationLog for auditability.
    """
    message = f"Your Smart Queue verification code is {code}. It expires in {OTP_EXPIRY_MINUTES} minutes."

    log = NotificationLog.objects.create(
        channel=NotificationLog.Channel.SMS,
        event_type=NotificationLog.EventType.OTP_VERIFICATION,
        recipient=phone_number,
        message=message,
        status=NotificationLog.Status.PENDING,
    )

    if settings.SMS_GATEWAY_API_KEY and settings.SMS_GATEWAY_URL:
        # Real dispatch wired up in the Notifications phase (Celery task +
        # actual HTTP call to the gateway). Left as a clear extension point.
        try:
            _dispatch_via_gateway(phone_number, message)
            log.status = NotificationLog.Status.SENT
            log.sent_at = timezone.now()
        except Exception as exc:  # noqa: BLE001 — log and continue, never crash registration on SMS failure
            log.status = NotificationLog.Status.FAILED
            log.failure_reason = str(exc)[:255]
        log.save(update_fields=["status", "sent_at", "failure_reason"])
    else:
        # No gateway configured yet — print to console so it's usable in dev.
        print(f"[DEV OTP] -> {phone_number}: {code}")  # noqa: T201
        log.status = NotificationLog.Status.SENT
        log.sent_at = timezone.now()
        log.save(update_fields=["status", "sent_at"])


def _dispatch_via_gateway(phone_number: str, message: str) -> None:
    import requests

    response = requests.post(
        settings.SMS_GATEWAY_URL,
        json={"api_key": settings.SMS_GATEWAY_API_KEY, "to": phone_number, "message": message},
        timeout=10,
    )
    response.raise_for_status()
