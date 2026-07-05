"""
Server-rendered auth pages. These render the styled templates for the
UI/UX Design phase; form submission is wired to the existing JWT/OTP API
(apps.accounts.api_views) via JS fetch in the Frontend Development phase.
"""
from django.views.generic import TemplateView


class LoginPageView(TemplateView):
    template_name = "auth/login.html"


class RegisterPageView(TemplateView):
    template_name = "auth/register.html"


class VerifyOTPPageView(TemplateView):
    template_name = "auth/verify_otp.html"


class ForgotPasswordPageView(TemplateView):
    template_name = "auth/forgot_password.html"


class ResetPasswordPageView(TemplateView):
    template_name = "auth/reset_password.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["uidb64"] = kwargs.get("uidb64")
        context["token"] = kwargs.get("token")
        return context
