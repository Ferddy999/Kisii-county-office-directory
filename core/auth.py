import logging

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from . import otp, throttle
from .roles import is_administrator

logger = logging.getLogger(__name__)


def landing_url(user, portal, next_url=""):
    """A deep link is honoured; otherwise land by the chosen portal."""
    if next_url and next_url != "/":
        return next_url
    if portal == "senior" or (portal is None and is_administrator(user)):
        return reverse("dashboard")
    return reverse("directory")


class RoleLoginForm(AuthenticationForm):
    portal = forms.ChoiceField(
        label="Sign in as",
        choices=[
            ("member", "Member: view and search the directory"),
            ("senior", "Senior officer (administrator): manage records and view the audit log"),
        ],
        widget=forms.RadioSelect,
        initial="member",
    )

    def clean(self):
        username = self.cleaned_data.get("username", "")
        if username and throttle.is_locked(self.request, username):
            logger.warning("Sign-in blocked for %s: too many failed attempts", username)
            raise forms.ValidationError(
                "Too many failed attempts. Please wait 15 minutes and try again.",
                code="locked",
            )
        try:
            cleaned = super().clean()
        except forms.ValidationError as error:
            if getattr(error, "code", None) == "invalid_login":
                throttle.register_failure(self.request, username)
                logger.warning("Failed sign-in for %s", username)
            raise
        throttle.clear(self.request, username)
        return cleaned

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if self.cleaned_data.get("portal") == "senior" and not is_administrator(user):
            raise forms.ValidationError(
                "This account does not have senior officer access. Choose Member to continue.",
                code="not_senior",
            )


class RoleLoginView(LoginView):
    authentication_form = RoleLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return landing_url(
            self.request.user, self.request.POST.get("portal"), self.get_redirect_url()
        )

    def form_valid(self, form):
        if not getattr(settings, "OTP_REQUIRED", True):
            return super().form_valid(form)
        try:
            otp.start(
                self.request, form.get_user(), form.cleaned_data["portal"], self.get_redirect_url()
            )
        except otp.NoContact:
            form.add_error(
                None,
                "No email address or phone number is saved on this account. "
                "Ask an administrator to add one.",
            )
            return self.form_invalid(form)
        except otp.SendFailed:
            form.add_error(None, "We could not send your code. Please try again in a moment.")
            return self.form_invalid(form)
        return redirect("login_verify")


@login_not_required
@require_http_methods(["GET", "POST"])
def login_verify(request):
    pending = request.session.get(otp.SESSION_KEY)
    if not pending:
        return redirect("login")
    error = ""
    if request.method == "POST":
        if "resend" in request.POST:
            try:
                otp.resend(request)
                messages.info(request, "A new code has been sent.")
                pending = request.session.get(otp.SESSION_KEY)
            except otp.TooSoon as exc:
                error = str(exc)
            except (otp.SendFailed, otp.NoContact):
                error = "We could not send a new code. Please try again."
        else:
            user, data, error, restart = otp.check(request, request.POST.get("code", ""))
            if restart:
                messages.error(request, error)
                return redirect("login")
            if user is not None:
                next_url = data["next"]
                if not url_has_allowed_host_and_scheme(
                    next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
                ):
                    next_url = ""
                login(request, user, backend=otp.BACKEND)
                return redirect(landing_url(user, data["portal"], next_url))
            pending = data or pending
    return render(request, "registration/login_verify.html", {
        "error": error,
        "destination": pending["shown"],
        "channel_label": "email" if pending["channel"] == "email" else "phone",
    })
