from contextvars import ContextVar

# The signed-in user for the request being handled (None outside a request).
current_user = ContextVar("audit_current_user", default=None)

# Set while a bulk cleanup runs, so it is summarised once instead of row by row.
suppressed = ContextVar("audit_suppressed", default=False)
