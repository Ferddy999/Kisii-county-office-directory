from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import StaffForm
from .models import Staff


class StaffPermission(PermissionRequiredMixin):
    raise_exception = True


class StaffList(StaffPermission, ListView):
    model = Staff
    permission_required = "staff.view_staff"
    paginate_by = 10

    def get_queryset(self):
        return Staff.objects.select_related("department", "office").order_by("full_name")


class StaffCreate(StaffPermission, SuccessMessageMixin, CreateView):
    model = Staff
    form_class = StaffForm
    permission_required = "staff.add_staff"
    success_url = reverse_lazy("staff_list")
    success_message = 'Staff member "%(full_name)s" was added.'


class StaffUpdate(StaffPermission, SuccessMessageMixin, UpdateView):
    model = Staff
    form_class = StaffForm
    permission_required = "staff.change_staff"
    success_url = reverse_lazy("staff_list")
    success_message = 'Staff member "%(full_name)s" was updated.'


class StaffDelete(StaffPermission, DeleteView):
    model = Staff
    permission_required = "staff.delete_staff"
    success_url = reverse_lazy("staff_list")

    def form_valid(self, form):
        name = self.object.full_name
        response = super().form_valid(form)
        messages.success(self.request, f'Staff member "{name}" was removed.')
        return response
