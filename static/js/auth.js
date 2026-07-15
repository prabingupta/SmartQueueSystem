/* Smart Queue Management System — wires the auth page forms (built in
   Phase 4) to the JWT/OTP API (built in Phase 3), and keeps the topbar
   in sync with client-side login state. */

(function () {
  "use strict";

  const DASHBOARD_URL = "/dashboard/citizen-preview/";
  const LOGIN_URL = "/accounts/login/";
  const VERIFY_OTP_URL = "/accounts/verify-otp/";
  const PENDING_PHONE_KEY = "sqms_pending_phone";

  function showFormError(form, message) {
    let banner = form.querySelector("[data-form-error]");
    if (!banner) {
      banner = document.createElement("div");
      banner.setAttribute("data-form-error", "");
      banner.className = "form-error";
      banner.style.cssText = "background:var(--crimson-soft); padding:var(--space-3); border-radius:var(--radius-md); margin-bottom:var(--space-4);";
      form.prepend(banner);
    }
    banner.textContent = message;
    banner.style.display = "block";
  }

  function clearFormError(form) {
    const banner = form.querySelector("[data-form-error]");
    if (banner) banner.style.display = "none";
  }

  function setLoading(button, loading, loadingText) {
    if (!button) return;
    if (loading) {
      button.dataset.originalText = button.textContent;
      button.textContent = loadingText || "Please wait…";
      button.disabled = true;
    } else {
      button.textContent = button.dataset.originalText || button.textContent;
      button.disabled = false;
    }
  }

  function wireRegisterForm() {
    const form = document.querySelector("[data-auth-form='register']");
    if (!form) return;
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearFormError(form);
      const button = form.querySelector("button[type='submit']");
      const payload = {
        username: form.username.value.trim(),
        email: form.email.value.trim(),
        phone_number: form.phone_number.value.trim(),
        first_name: form.first_name.value.trim(),
        last_name: form.last_name.value.trim(),
        password: form.password.value,
        password_confirm: form.password_confirm.value,
      };
      setLoading(button, true, "Creating account…");
      try {
        await SQMSApi.post("/register/", payload);
        sessionStorage.setItem(PENDING_PHONE_KEY, payload.phone_number);
        window.location.href = VERIFY_OTP_URL;
      } catch (err) {
        showFormError(form, err.message);
        setLoading(button, false);
      }
    });
  }

  function wireVerifyOtpForm() {
    const form = document.querySelector("[data-auth-form='verify-otp']");
    if (!form) return;

    const phone = sessionStorage.getItem(PENDING_PHONE_KEY);
    const phoneDisplay = form.querySelector("[data-phone-display]");
    if (phone && phoneDisplay) phoneDisplay.textContent = phone;

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearFormError(form);
      if (!phone) {
        showFormError(form, "We couldn't find a pending registration. Please register again.");
        return;
      }
      const button = form.querySelector("button[type='submit']");
      setLoading(button, true, "Verifying…");
      try {
        await SQMSApi.post("/verify-otp/", { phone_number: phone, code: form.code.value.trim(), purpose: "registration" });
        sessionStorage.removeItem(PENDING_PHONE_KEY);
        window.showToast && window.showToast("Phone verified. You can now log in.");
        window.location.href = LOGIN_URL;
      } catch (err) {
        showFormError(form, err.message);
        setLoading(button, false);
      }
    });

    const resendBtn = form.querySelector("[data-resend-otp]");
    if (resendBtn) {
      resendBtn.addEventListener("click", async () => {
        if (!phone) return;
        resendBtn.disabled = true;
        try {
          await SQMSApi.post("/resend-otp/", { phone_number: phone, purpose: "registration" });
          window.showToast && window.showToast("A new code has been sent.");
        } catch (err) {
          showFormError(form, err.message);
        } finally {
          setTimeout(() => { resendBtn.disabled = false; }, 15000);
        }
      });
    }
  }

  function wireLoginForm() {
    const form = document.querySelector("[data-auth-form='login']");
    if (!form) return;
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearFormError(form);
      const button = form.querySelector("button[type='submit']");
      setLoading(button, true, "Logging in…");
      try {
        const data = await SQMSApi.post("/login/", { username: form.username.value.trim(), password: form.password.value });
        SQMSApi.setSession(data.access, data.refresh, data.user);
        window.location.href = DASHBOARD_URL;
      } catch (err) {
        showFormError(form, err.message);
        setLoading(button, false);
      }
    });
  }

  function wireForgotPasswordForm() {
    const form = document.querySelector("[data-auth-form='forgot-password']");
    if (!form) return;
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearFormError(form);
      const button = form.querySelector("button[type='submit']");
      setLoading(button, true, "Sending…");
      try {
        const data = await SQMSApi.post("/password-reset/request/", { email: form.email.value.trim() });
        form.innerHTML = `<p class="text-soft">${data.detail}</p>`;
      } catch (err) {
        showFormError(form, err.message);
        setLoading(button, false);
      }
    });
  }

  function wireResetPasswordForm() {
    const form = document.querySelector("[data-auth-form='reset-password']");
    if (!form) return;
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      clearFormError(form);
      if (form.new_password.value !== form.confirm_password.value) {
        showFormError(form, "Passwords do not match.");
        return;
      }
      const button = form.querySelector("button[type='submit']");
      setLoading(button, true, "Resetting…");
      try {
        await SQMSApi.post("/password-reset/confirm/", {
          uid: form.uid.value, token: form.token.value, new_password: form.new_password.value,
        });
        window.showToast && window.showToast("Password reset. Please log in.");
        window.location.href = LOGIN_URL;
      } catch (err) {
        showFormError(form, err.message);
        setLoading(button, false);
      }
    });
  }

  function updateTopbarAuthState() {
    const guest = document.querySelector("[data-auth-guest]");
    const authed = document.querySelector("[data-auth-user]");
    if (!guest || !authed) return;
    if (SQMSApi.isAuthenticated()) {
      guest.style.display = "none";
      authed.style.display = "flex";
    } else {
      guest.style.display = "flex";
      authed.style.display = "none";
    }
  }

  function wireLogoutButtons() {
    document.querySelectorAll("[data-logout]").forEach((btn) => {
      btn.addEventListener("click", async (event) => {
        event.preventDefault();
        const refresh = SQMSApi.getRefreshToken();
        try {
          if (refresh) {
            await fetch("/api/v1/accounts/logout/", {
              method: "POST",
              headers: { "Content-Type": "application/json", Authorization: `Bearer ${SQMSApi.getAccessToken()}` },
              body: JSON.stringify({ refresh }),
            });
          }
        } catch (err) {
          // Non-fatal — clear the local session regardless.
        }
        SQMSApi.clearSession();
        window.location.href = "/";
      });
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    wireRegisterForm();
    wireVerifyOtpForm();
    wireLoginForm();
    wireForgotPasswordForm();
    wireResetPasswordForm();
    updateTopbarAuthState();
    wireLogoutButtons();
  });
})();
