from django.db.models import Q

from offices.models import Office
from staff.models import Staff


def search_staff(filters):
    results = Staff.objects.filter(is_active=True).select_related("department", "office")
    text = filters.get("q")
    if text:
        results = results.filter(
            Q(full_name__icontains=text)
            | Q(designation__icontains=text)
            | Q(department__name__icontains=text)
            | Q(office__name__icontains=text)
            | Q(office__building__icontains=text)
            | Q(office__services__name__icontains=text)
        )
    if filters.get("department"):
        results = results.filter(department=filters["department"])
    if filters.get("office"):
        results = results.filter(office=filters["office"])
    if filters.get("building"):
        results = results.filter(office__building=filters["building"])
    if filters.get("service"):
        results = results.filter(office__services=filters["service"])
    return results.distinct()


def search_offices(filters):
    results = (
        Office.objects.filter(is_active=True)
        .select_related("department")
        .prefetch_related("services")
    )
    text = filters.get("q")
    if text:
        results = results.filter(
            Q(name__icontains=text)
            | Q(department__name__icontains=text)
            | Q(building__icontains=text)
            | Q(email__icontains=text)
            | Q(services__name__icontains=text)
        )
    if filters.get("department"):
        results = results.filter(department=filters["department"])
    if filters.get("office"):
        results = results.filter(pk=filters["office"].pk)
    if filters.get("building"):
        results = results.filter(building=filters["building"])
    if filters.get("service"):
        results = results.filter(services=filters["service"])
    return results.distinct()
