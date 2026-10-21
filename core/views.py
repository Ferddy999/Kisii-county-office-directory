from django.db.models import Count
from django.shortcuts import render

from audit.models import AuditLog
from departments.models import Department, Directorate
from offices.models import Office
from staff.models import Staff


def dashboard(request):
    departments = Department.objects.annotate(
        office_count=Count("offices", distinct=True),
        staff_count=Count("staff_members", distinct=True),
    )
    totals = [
        {"label": "Departments", "value": departments.count(), "note": "Registered"},
        {"label": "Directorates", "value": Directorate.objects.count(), "note": "Registered"},
        {"label": "Offices", "value": Office.objects.filter(is_active=True).count(), "note": "Active"},
        {"label": "Staff entries", "value": Staff.objects.filter(is_active=True).count(), "note": "Active"},
    ]
    can_see_audit = request.user.has_perm("audit.view_auditlog")
    context = {
        "totals": totals,
        "departments": departments,
        "recent_changes": AuditLog.objects.all()[:5] if can_see_audit else [],
    }
    return render(request, "core/dashboard.html", context)
