from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods

from .auth import landing_url
from .legal import COOKIE_AGE, COOKIE_CHOICES, COOKIE_NAME, TERMS_VERSION
from .middleware import has_accepted_terms
from .models import ConsentLog


def _safe_next(request, fallback):
    target = request.POST.get("next") or request.GET.get("next") or ""
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return target
    return fallback


@login_not_required
def terms(request):
    return render(request, "legal/terms.html")


@login_not_required
def privacy(request):
    return render(request, "legal/privacy.html")


@login_not_required
@require_http_methods(["GET", "POST"])
def cookie_settings(request):
    if request.method == "POST":
        choice = request.POST.get("choice")
        if choice not in COOKIE_CHOICES:
            choice = "essential"
        if request.user.is_authenticated:
            ConsentLog.objects.create(
                user=request.user,
                username=request.user.get_username(),
                kind=ConsentLog.COOKIES,
                choice=choice,
            )
        messages.success(request, "Your cookie choice has been saved.")
        response = redirect(_safe_next(request, reverse("cookie_settings")))
        response.set_cookie(
            COOKIE_NAME, choice, max_age=COOKIE_AGE, samesite="Lax",
            secure=request.is_secure(), httponly=True,
        )
        return response
    current = request.COOKIES.get(COOKIE_NAME, "")
    return render(request, "legal/cookie_settings.html", {
        "current": current if current in COOKIE_CHOICES else "essential",
        "next": _safe_next(request, ""),
    })


@require_http_methods(["GET", "POST"])
def accept_terms(request):
    destination = landing_url(request.user, None, _safe_next(request, ""))
    if has_accepted_terms(request.user):
        request.session["terms_version"] = TERMS_VERSION
        return redirect(destination)
    error = ""
    if request.method == "POST":
        if request.POST.get("agree"):
            ConsentLog.objects.create(
                user=request.user,
                username=request.user.get_username(),
                kind=ConsentLog.TERMS,
                version=TERMS_VERSION,
                choice="accepted",
            )
            request.session["terms_version"] = TERMS_VERSION
            return redirect(destination)
        error = "Tick the box to confirm you accept, or decline to sign out."
    return render(request, "legal/accept_terms.html", {
        "error": error,
        "next": request.GET.get("next") or request.POST.get("next") or "",
    })
