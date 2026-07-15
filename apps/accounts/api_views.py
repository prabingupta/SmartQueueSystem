"""
Authentication API views. Registration issues an OTP instead of activating
the account immediately; login is JWT-based via CustomTokenObtainPairView.
"""
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import PhoneOTP
from apps.accounts.otp_service import issue_otp
from apps.accounts.permissions import IsAdminRole
from apps.accounts.serializers import (
    CustomTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileSerializer,
    RegisterSerializer,
    ResendOTPSerializer,
    StaffCreateSerializer,
    VerifyOTPSerializer,
)

User = get_user_model()


class OTPThrottle(AnonRateThrottle):
    scope = "otp"


def _attach_dev_otp(payload, otp):
    """
    Dev convenience only: when DEBUG is on and no real SMS gateway is
    configured, echo the OTP code back in the API response so it can be
    shown directly in the browser instead of requiring terminal/DB access.
    Hard-gated on settings.DEBUG — never runs in production.
    """
    from django.conf import settings

    if settings.DEBUG and not (settings.SMS_GATEWAY_API_KEY and settings.SMS_GATEWAY_URL):
        payload["dev_otp_code"] = otp.code


class RegisterView(generics.CreateAPIView):
    """Creates an inactive citizen account and sends a registration OTP."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [OTPThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        otp = issue_otp(user, user.phone_number, PhoneOTP.Purpose.REGISTRATION)
        payload = {
            "detail": "Registration successful. Enter the OTP sent to your phone to activate your account.",
            "phone_number": user.phone_number,
        }
        _attach_dev_otp(payload, otp)
        return Response(payload, status=status.HTTP_201_CREATED)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPThrottle]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = serializer.validated_data["otp"]

        otp.is_used = True
        otp.save(update_fields=["is_used"])

        user = otp.user
        user.phone_verified = True
        if otp.purpose == PhoneOTP.Purpose.REGISTRATION:
            user.is_active = True
        user.save(update_fields=["phone_verified", "is_active"])

        return Response({"detail": "Phone number verified successfully."}, status=status.HTTP_200_OK)


class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPThrottle]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(phone_number=serializer.validated_data["phone_number"])
        otp = issue_otp(user, user.phone_number, serializer.validated_data["purpose"])
        payload = {"detail": "A new verification code has been sent."}
        _attach_dev_otp(payload, otp)
        return Response(payload, status=status.HTTP_200_OK)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
        except KeyError:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:  # noqa: BLE001 — invalid/expired token is fine to no-op on logout
            pass
        return Response({"detail": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "If an account exists with this email, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class StaffCreateView(generics.CreateAPIView):
    """Admin-only endpoint to provision Reception/Operator/Manager/District Admin/Supervisor accounts."""
    queryset = User.objects.all()
    serializer_class = StaffCreateSerializer
    permission_classes = [IsAdminRole]
