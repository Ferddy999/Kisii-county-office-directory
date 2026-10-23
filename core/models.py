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
