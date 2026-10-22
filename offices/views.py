from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import OfficeForm
from .models import Office


class OfficePermission(PermissionRequiredMixin):
    raise_exception = True


class OfficeList(OfficePermission, ListView):
    model = Office
    permission_required = "offices.view_office"
    paginate_by = 10

    def get_queryset(self):
        return Office.objects.select_related("department").order_by(
            "department__name", "name"
        )


class OfficeCreate(OfficePermission, SuccessMessageMixin, CreateView):
    model = Office
    form_class = OfficeForm
    permission_required = "offices.add_office"
    success_url = reverse_lazy("office_list")
    success_message = 'Office "%(name)s" was added.'


class OfficeUpdate(OfficePermission, SuccessMessageMixin, UpdateView):
    model = Office
    form_class = OfficeForm
    permission_required = "offices.change_office"
    success_url = reverse_lazy("office_list")
    success_message = 'Office "%(name)s" was updated.'


class OfficeDelete(OfficePermission, DeleteView):
    model = Office
    permission_required = "offices.delete_office"
    success_url = reverse_lazy("office_list")

    def form_valid(self, form):
        name = self.object.name
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                f'"{name}" still has staff assigned, so it cannot be deleted. '
                "Move or remove them first.",
            )
            return redirect("office_list")
        messages.success(self.request, f'Office "{name}" was deleted.')
        return response
