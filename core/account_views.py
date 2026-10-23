from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import ProtectedError
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from audit.context import suppressed
from audit.models import AuditLog
from offices.models import Office, Service
from staff.models import Staff

from .account_forms import AccountForm, HandoverForm
from .models import UserProfile
from .roles import is_administrator


def account_settings(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    form = AccountForm(request.POST or None, user=request.user, profile=profile)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your details have been saved.")
        return redirect("account_settings")
    return render(request, "core/settings.html", {"form": form})


class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = "core/password_change.html"
    success_url = reverse_lazy("account_settings")
    success_message = "Your password has been changed."


def handover(request):
    if not is_administrator(request.user):
        raise PermissionDenied
    form = HandoverForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        targets = form.cleaned_data["targets"]
        removed = []
        token = suppressed.set(True)
        try:
            with transaction.atomic():
                if "staff" in targets:
                    removed.append(f"{Staff.objects.all().delete()[0]} staff")
                if "offices" in targets:
                    removed.append(f"{Office.objects.all().delete()[0]} offices")
                if "services" in targets:
                    removed.append(f"{Service.objects.all().delete()[0]} services")
                if "users" in targets:
                    others = get_user_model().objects.filter(is_superuser=False).exclude(pk=request.user.pk)
                    removed.append(f"{others.delete()[0]} user rows")
                if "audit" in targets:
                    removed.append(f"{AuditLog.objects.all().delete()[0]} audit entries")
        except ProtectedError:
            form.add_error(None, "Offices that still have staff cannot be deleted. Tick the staff records too.")
        else:
            AuditLog.objects.create(
                user=request.user,
                username=request.user.get_username(),
                action="delete",
                model_name="handover cleanup",
                object_id=0,
                object_repr="Removed: " + ", ".join(removed),
                changes={},
            )
            messages.success(request, "Handover cleanup finished. " + ", ".join(removed) + " removed.")
            return redirect("account_settings")
        finally:
            suppressed.reset(token)
    return render(request, "core/handover.html", {"form": form})
