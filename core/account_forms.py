import re

from django import forms
from django.contrib.auth import get_user_model

from audit.models import AuditLog
from offices.models import Office, Service
from staff.models import Staff

from .models import UserProfile

User = get_user_model()


def normalise_phone(raw):
    digits = re.sub(r"[\s\-()]", "", raw or "")
    if not digits:
        return ""
    if digits.startswith("254"):
        digits = "+" + digits
    elif digits.startswith("0"):
        digits = "+254" + digits[1:]
    elif re.fullmatch(r"[71]\d{8}", digits):
        digits = "+254" + digits
    if not re.fullmatch(r"\+254\d{9}", digits):
        raise forms.ValidationError("Enter a Kenyan number such as 0712 345 678.")
    return digits


class AccountForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(label="Email address", required=False)
    phone = forms.CharField(label="Phone number", required=False, help_text="For example 0712 345 678.")
    otp_channel = forms.ChoiceField(
        label="Send my sign-in code by",
        choices=UserProfile.CHANNELS,
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, user, profile, **kwargs):
        self.user = user
        self.profile = profile
        if not args and "data" not in kwargs:
            kwargs["initial"] = {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone": profile.phone,
                "otp_channel": profile.otp_channel,
            }
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if email and User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("Another account already uses this email address.")
        return email

    def clean_phone(self):
        return normalise_phone(self.cleaned_data["phone"])

    def clean(self):
        data = super().clean()
        email, phone, channel = data.get("email"), data.get("phone"), data.get("otp_channel")
        if "email" in self.errors or "phone" in self.errors:
            return data
        if not email and not phone:
            raise forms.ValidationError("Save at least an email address or a phone number so we can send your sign-in code.")
        if channel == "email" and not email:
            self.add_error("email", "Add an email address, or choose SMS.")
        if channel == "sms" and not phone:
            self.add_error("phone", "Add a phone number, or choose email.")
        return data

    def save(self):
        d = self.cleaned_data
        self.user.first_name = d["first_name"]
        self.user.last_name = d["last_name"]
        self.user.email = d["email"]
        self.user.save(update_fields=["first_name", "last_name", "email"])
        self.profile.phone = d["phone"]
        self.profile.otp_channel = d["otp_channel"]
        self.profile.save()


class HandoverForm(forms.Form):
    targets = forms.MultipleChoiceField(
        label="What to delete",
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        error_messages={"required": "Choose at least one thing to delete."},
    )
    password = forms.CharField(label="Your password", widget=forms.PasswordInput)
    confirm = forms.CharField(label="Type DELETE to confirm")

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        others = User.objects.filter(is_superuser=False).exclude(pk=user.pk).count()
        self.fields["targets"].choices = [
            ("staff", f"All staff records ({Staff.objects.count()})"),
            ("offices", f"All offices ({Office.objects.count()})"),
            ("services", f"All services ({Service.objects.count()})"),
            ("users", f"Other test user accounts, not administrators or you ({others})"),
            ("audit", f"The audit log ({AuditLog.objects.count()})"),
        ]

    def clean_password(self):
        if not self.user.check_password(self.cleaned_data["password"]):
            raise forms.ValidationError("That password is not correct.")
        return self.cleaned_data["password"]

    def clean_confirm(self):
        if self.cleaned_data["confirm"].strip() != "DELETE":
            raise forms.ValidationError("Type the word DELETE in capital letters.")
        return "DELETE"
