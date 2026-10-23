import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


def send_sms(phone, message):
    """Send one text message.

    SMS_BACKEND=console prints the message in the terminal (development).
    A real gateway (for example Africa's Talking) is added here once the
    county ICT provides the account details.
    """
    backend = getattr(settings, "SMS_BACKEND", "console")
    if backend == "console":
        print(f"\n[SMS to {phone}] {message}\n")
        return
    raise ImproperlyConfigured(f"SMS backend '{backend}' is not configured.")
