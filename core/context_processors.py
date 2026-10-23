from django.conf import settings

from .legal import COOKIE_NAME, TERMS_VERSION, UPDATED
from .roles import is_administrator


def role(request):
    context = {
        "cookie_choice": request.COOKIES.get(COOKIE_NAME, ""),
        "legal": {
            "contact_email": getattr(settings, "LEGAL_CONTACT_EMAIL", "ict@example.go.ke"),
            "version": TERMS_VERSION,
            "updated": UPDATED,
        },
    }
    user = request.user
    if user.is_authenticated:
        admin = is_administrator(user)
        context["is_administrator"] = admin
        context["role_label"] = "Administrator" if admin else "Ordinary user"
    return context
