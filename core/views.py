from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render

from audit.models import AuditLog
from departments.models import Department, Directorate
from offices.models import Office
from staff.models import Staff

from .forms import DirectoryFilterForm
from .search import search_offices, search_staff

PAGE_SIZE = 8


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


@permission_required(["staff.view_staff", "offices.view_office"], raise_exception=True)
def directory(request):
    tab = "offices" if request.GET.get("tab") == "offices" else "staff"
    form = DirectoryFilterForm(request.GET or None)
    filters = form.cleaned_data if form.is_valid() else {}

    search = search_offices if tab == "offices" else search_staff
    paginator = Paginator(search(filters), PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)
    params["tab"] = tab
    base_query = params.urlencode() + "&"

    tab_queries = {}
    for name in ("staff", "offices"):
        tab_params = params.copy()
        tab_params["tab"] = name
        tab_queries[name] = tab_params.urlencode()

    context = {
        "form": form,
        "tab": tab,
        "page": page,
        "page_numbers": list(
            paginator.get_elided_page_range(page.number, on_each_side=1, on_ends=1)
        ),
        "ellipsis": Paginator.ELLIPSIS,
        "base_query": base_query,
        "staff_tab_query": tab_queries["staff"],
        "offices_tab_query": tab_queries["offices"],
    }
    return render(request, "core/directory.html", context)
