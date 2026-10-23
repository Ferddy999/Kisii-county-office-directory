from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse

from .legal import TERMS_VERSION
from .models import ConsentLog

EXEMPT_PREFIXES = ("/terms/", "/privacy/", "/cookies/", "/logout/", "/static/")


def has_accepted_terms(user):
    return ConsentLog.objects.filter(
        user=user, kind=ConsentLog.TERMS, version=TERMS_VERSION, choice="accepted"
    ).exists()


class TermsAcceptanceMiddleware:
    """Signed-in users must accept the current Terms before using the system."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if (
            user is not None
            and user.is_authenticated
            and not request.path.startswith(EXEMPT_PREFIXES)
            and request.session.get("terms_version") != TERMS_VERSION
        ):
            if has_accepted_terms(user):
                request.session["terms_version"] = TERMS_VERSION
            else:
                query = urlencode({"next": request.get_full_path()})
                return redirect(f"{reverse('accept_terms')}?{query}")
        return self.get_response(request)
