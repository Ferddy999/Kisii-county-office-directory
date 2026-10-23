from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse

from .roles import is_administrator


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
        # A deep link (for example /staff/) is honoured; otherwise land by role.
        next_url = self.get_redirect_url()
        if next_url and next_url != "/":
            return next_url
        portal = self.request.POST.get("portal")
        if portal == "senior" or (portal is None and is_administrator(self.request.user)):
            return reverse("dashboard")
        return reverse("directory")
