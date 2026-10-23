from contextvars import ContextVar

# The signed-in user for the request being handled (None outside a request).
current_user = ContextVar("audit_current_user", default=None)
