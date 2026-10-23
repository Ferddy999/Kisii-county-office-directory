from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserProfile(TimeStampedModel):
    """Contact details used for sign-in codes. One per user account."""

    CHANNELS = [
        ("email", "Email"),
        ("sms", "SMS to my phone"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    phone = models.CharField(
        max_length=13,
        blank=True,
        validators=[RegexValidator(r"^\+254\d{9}$", "Use the format +254XXXXXXXXX.")],
    )
    otp_channel = models.CharField(max_length=5, choices=CHANNELS, default="email")

    def __str__(self):
        return f"Profile of {self.user}"


class ConsentLog(models.Model):
    """Append-only record of terms acceptance and cookie choices."""

    TERMS = "terms"
    COOKIES = "cookies"
    KINDS = [(TERMS, "Terms and Conditions"), (COOKIES, "Cookies")]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="consent_logs",
    )
    username = models.CharField(max_length=150, blank=True)
    kind = models.CharField(max_length=10, choices=KINDS)
    version = models.CharField(max_length=20, blank=True)
    choice = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.username}: {self.kind} {self.choice}"
