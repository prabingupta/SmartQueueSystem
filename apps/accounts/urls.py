"""Server-rendered auth page routes (styled pages; API in api_urls.py handles logic)."""
from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.LoginPageView.as_view(), name="login"),
    path("register/", views.RegisterPageView.as_view(), name="register"),
    path("verify-otp/", views.VerifyOTPPageView.as_view(), name="verify-otp"),
    path("forgot-password/", views.ForgotPasswordPageView.as_view(), name="forgot-password"),
    path("reset-password/confirm/<str:uidb64>/<str:token>/", views.ResetPasswordPageView.as_view(), name="reset-password-confirm"),
]
