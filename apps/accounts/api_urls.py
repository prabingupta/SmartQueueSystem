"""API routes for authentication, mounted under /api/v1/accounts/."""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts import api_views

app_name = "accounts_api"

urlpatterns = [
    path("register/", api_views.RegisterView.as_view(), name="register"),
    path("verify-otp/", api_views.VerifyOTPView.as_view(), name="verify-otp"),
    path("resend-otp/", api_views.ResendOTPView.as_view(), name="resend-otp"),

    path("login/", api_views.CustomTokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", api_views.LogoutView.as_view(), name="logout"),

    path("password-reset/request/", api_views.PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset/confirm/", api_views.PasswordResetConfirmView.as_view(), name="password-reset-confirm"),

    path("profile/", api_views.ProfileView.as_view(), name="profile"),
    path("staff/create/", api_views.StaffCreateView.as_view(), name="staff-create"),
]
