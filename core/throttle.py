"""Lock an account for a while after repeated wrong passwords."""
import hashlib

from django.core.cache import cache

MAX_FAILURES = 5  # the lock lasts as long as the cache TIMEOUT in settings (15 minutes)


def _key(request, username):
    ip = request.META.get("REMOTE_ADDR", "")
    raw = f"{(username or '').strip().lower()}|{ip}"
    return "loginfail:" + hashlib.sha256(raw.encode()).hexdigest()


def is_locked(request, username):
    return (cache.get(_key(request, username)) or 0) >= MAX_FAILURES


def register_failure(request, username):
    key = _key(request, username)
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1)


def clear(request, username):
    cache.delete(_key(request, username))
