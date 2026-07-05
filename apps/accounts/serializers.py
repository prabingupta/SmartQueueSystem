"""
Serializers for the authentication API: registration + OTP verification,
login (JWT with extra claims), password reset, profile, and admin-created
staff accounts.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import PhoneOTP

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "phone_number", "first_name", "last_name", "password", "password_confirm"]

    def validate_phone_number(self, value):
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("An account with this phone number already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(role=User.Role.CITIZEN, is_active=False, **validated_data)
        user.set_password(password)
        user.save()
        return user


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    code = serializers.CharField(max_length=6, min_length=6)
    purpose = serializers.ChoiceField(choices=PhoneOTP.Purpose.choices, default=PhoneOTP.Purpose.REGISTRATION)

    def validate(self, attrs):
        try:
            otp = PhoneOTP.objects.filter(
                phone_number=attrs["phone_number"], purpose=attrs["purpose"], is_used=False,
            ).latest("created_at")
        except PhoneOTP.DoesNotExist:
            raise serializers.ValidationError("No pending verification code for this number.")

        if otp.is_expired:
            raise serializers.ValidationError("This code has expired. Please request a new one.")
        if otp.attempts >= otp.max_attempts:
            raise serializers.ValidationError("Too many incorrect attempts. Please request a new code.")
        if otp.code != attrs["code"]:
            otp.attempts += 1
            otp.save(update_fields=["attempts"])
            raise serializers.ValidationError("Incorrect verification code.")

        attrs["otp"] = otp
        return attrs


class ResendOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    purpose = serializers.ChoiceField(choices=PhoneOTP.Purpose.choices, default=PhoneOTP.Purpose.REGISTRATION)

    def validate_phone_number(self, value):
        if not User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("No account found with this phone number.")
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds role/name claims to the JWT and blocks login for unverified accounts."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["full_name"] = user.get_full_name()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_active:
            raise serializers.ValidationError("Account is not active. Please verify your phone number first.")
        data["user"] = {
            "id": str(self.user.public_id),
            "username": self.user.username,
            "full_name": self.user.get_full_name(),
            "role": self.user.role,
            "office_id": str(self.user.office.public_id) if self.user.office_id else None,
        }
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        email = self.validated_data["email"]
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            # Deliberately silent — don't reveal whether an email is registered.
            return
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        self.reset_link = f"/accounts/reset-password/confirm/{uid}/{token}/"
        self._send_email(user, self.reset_link)

    @staticmethod
    def _send_email(user, reset_link):
        from django.conf import settings
        from django.core.mail import send_mail

        send_mail(
            subject="Reset your Smart Queue password",
            message=f"Hello {user.get_full_name() or user.username},\n\n"
                    f"Use the link below to reset your password:\n{reset_link}\n\n"
                    f"If you didn't request this, you can ignore this email.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])

    def validate(self, attrs):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            raise serializers.ValidationError("Invalid reset link.")

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError("This reset link is invalid or has expired.")

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class ProfileSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)
    office_name = serializers.CharField(source="office.name", read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            "public_id", "username", "email", "phone_number", "first_name", "last_name",
            "role", "role_display", "office", "office_name", "date_of_birth", "profile_photo",
            "address", "preferred_language", "phone_verified", "email_verified",
        ]
        read_only_fields = ["public_id", "username", "role", "office", "phone_verified", "email_verified"]


class StaffCreateSerializer(serializers.ModelSerializer):
    """Admin-only: creates staff accounts directly active, no OTP step (trusted provisioning)."""

    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            "username", "email", "phone_number", "first_name", "last_name",
            "password", "role", "office", "district",
        ]

    def validate_role(self, value):
        if value == User.Role.CITIZEN:
            raise serializers.ValidationError("Use the public registration endpoint for citizen accounts.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(is_active=True, phone_verified=True, email_verified=True, **validated_data)
        user.set_password(password)
        user.save()
        return user
