import logging
import secrets
import time

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.crypto import constant_time_compare, salted_hmac

from .models import UserProfile
from .sms import send_sms

logger = logging.getLogger(__name__)

SESSION_KEY = "pending_login"
BACKEND = "django.contrib.auth.backends.ModelBackend"
CODE_TTL = 5 * 60
RESEND_AFTER = 30
MAX_ATTEMPTS = 5
MAX_SENDS = 5


class NoContact(Exception):
    pass


class SendFailed(Exception):
    pass


class TooSoon(Exception):
    pass


def _digest(uid, code):
    return salted_hmac("core.otp", f"{uid}:{code}").hexdigest()


def mask(channel, destination):
    if channel == "email":
        local, _, domain = destination.partition("@")
        return f"{local[:1]}***@{domain}"
    return f"{destination[:4]}*****{destination[-3:]}"


def _channel_for(user):
    profile = UserProfile.objects.filter(user=user).first()
    preferred = profile.otp_channel if profile else "email"
    options = {"email": user.email, "sms": profile.phone if profile else ""}
    order = [preferred] + [c for c in options if c != preferred]
    for channel in order:
        if options[channel]:
            return channel, options[channel]
    raise NoContact


def _deliver(channel, destination, code):
    message = (
        f"Your Kisii County Office Directory code is {code}. "
        "It expires in 5 minutes. Do not share it with anyone."
    )
    try:
        if channel == "email":
            send_mail("Your sign-in code", message, None, [destination])
        else:
            send_sms(destination, message)
    except Exception as exc:
        logger.exception("Could not deliver the sign-in code")
        raise SendFailed from exc


def _issue(request, user, portal, next_url, attempts=0, sends=0):
    channel, destination = _channel_for(user)
    code = f"{secrets.randbelow(10**6):06d}"
    _deliver(channel, destination, code)
    now = time.time()
    request.session[SESSION_KEY] = {
        "uid": user.pk,
        "portal": portal,
        "next": next_url or "",
        "hash": _digest(user.pk, code),
        "expires": now + CODE_TTL,
        "sent_at": now,
        "attempts": attempts,
        "sends": sends + 1,
        "channel": channel,
        "shown": mask(channel, destination),
    }


def start(request, user, portal, next_url):
    _issue(request, user, portal, next_url)


def resend(request):
    pending = request.session.get(SESSION_KEY)
    if not pending:
        raise TooSoon("Your sign-in session expired. Please sign in again.")
    wait = int(pending["sent_at"] + RESEND_AFTER - time.time())
    if wait > 0:
        raise TooSoon(f"Please wait {wait} seconds before asking for a new code.")
    if pending["sends"] >= MAX_SENDS:
        raise TooSoon("Too many codes requested. Please sign in again later.")
    user = get_user_model().objects.filter(pk=pending["uid"], is_active=True).first()
    if user is None:
        raise TooSoon("Your sign-in session expired. Please sign in again.")
    _issue(
        request, user, pending["portal"], pending["next"],
        attempts=pending["attempts"], sends=pending["sends"],
    )


def check(request, code):
    """Return (user, pending, error, restart)."""
    pending = request.session.get(SESSION_KEY)
    if not pending:
        return None, None, "Your sign-in session expired. Please sign in again.", True
    if time.time() > pending["expires"]:
        request.session.pop(SESSION_KEY, None)
        return None, None, "That code has expired. Please sign in again.", True
    if pending["attempts"] >= MAX_ATTEMPTS:
        request.session.pop(SESSION_KEY, None)
        return None, None, "Too many wrong codes. Please sign in again.", True
    pending["attempts"] += 1
    request.session[SESSION_KEY] = pending
    if not constant_time_compare(_digest(pending["uid"], (code or "").strip()), pending["hash"]):
        left = MAX_ATTEMPTS - pending["attempts"]
        return None, pending, f"That code is not correct. {left} tries left.", False
    user = get_user_model().objects.filter(pk=pending["uid"], is_active=True).first()
    request.session.pop(SESSION_KEY, None)
    if user is None:
        return None, None, "This account is no longer active.", True
    return user, pending, "", False
