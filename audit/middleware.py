from .context import current_user


class AuditUserMiddleware:
    """Remember who is making the request so signals can record it."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = current_user.set(getattr(request, "user", None))
        try:
            return self.get_response(request)
        finally:
            current_user.reset(token)
