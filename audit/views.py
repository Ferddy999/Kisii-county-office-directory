from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView

from .models import AuditLog


class AuditLogList(PermissionRequiredMixin, ListView):
    model = AuditLog
    permission_required = "audit.view_auditlog"
    raise_exception = True
    paginate_by = 15
