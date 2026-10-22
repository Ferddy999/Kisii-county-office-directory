from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import DepartmentForm, DirectorateForm
from .models import Department, Directorate


class Restricted(PermissionRequiredMixin):
    raise_exception = True


class SafeDelete:
    """Refuse politely when other records still depend on the one being deleted."""

    label = "Record"
    list_url_name = ""

    def form_valid(self, form):
        name = str(self.object)
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                f'"{name}" is still in use, so it cannot be deleted. '
                "Remove or move what depends on it first.",
            )
            return redirect(self.list_url_name)
        messages.success(self.request, f'{self.label} "{name}" was deleted.')
        return response


class DepartmentList(Restricted, ListView):
    model = Department
    permission_required = "departments.view_department"
    paginate_by = 10

    def get_queryset(self):
        return Department.objects.annotate(
            directorate_count=Count("directorates", distinct=True),
            office_count=Count("offices", distinct=True),
            staff_count=Count("staff_members", distinct=True),
        ).order_by("name")


class DepartmentCreate(Restricted, SuccessMessageMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    permission_required = "departments.add_department"
    success_url = reverse_lazy("department_list")
    success_message = 'Department "%(name)s" was added.'


class DepartmentUpdate(Restricted, SuccessMessageMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    permission_required = "departments.change_department"
    success_url = reverse_lazy("department_list")
    success_message = 'Department "%(name)s" was updated.'


class DepartmentDelete(Restricted, SafeDelete, DeleteView):
    model = Department
    permission_required = "departments.delete_department"
    success_url = reverse_lazy("department_list")
    label = "Department"
    list_url_name = "department_list"


class DirectorateList(Restricted, ListView):
    model = Directorate
    permission_required = "departments.view_directorate"
    paginate_by = 10

    def get_queryset(self):
        return Directorate.objects.select_related("department").order_by(
            "department__name", "name"
        )


class DirectorateCreate(Restricted, SuccessMessageMixin, CreateView):
    model = Directorate
    form_class = DirectorateForm
    permission_required = "departments.add_directorate"
    success_url = reverse_lazy("directorate_list")
    success_message = 'Directorate "%(name)s" was added.'


class DirectorateUpdate(Restricted, SuccessMessageMixin, UpdateView):
    model = Directorate
    form_class = DirectorateForm
    permission_required = "departments.change_directorate"
    success_url = reverse_lazy("directorate_list")
    success_message = 'Directorate "%(name)s" was updated.'


class DirectorateDelete(Restricted, SafeDelete, DeleteView):
    model = Directorate
    permission_required = "departments.delete_directorate"
    success_url = reverse_lazy("directorate_list")
    label = "Directorate"
    list_url_name = "directorate_list"
