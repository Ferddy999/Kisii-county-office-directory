from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from core.roles import ADMIN_GROUP, USER_GROUP

DIRECTORY_MODELS = {
    "departments": ["department", "directorate"],
    "offices": ["office", "service"],
    "staff": ["staff"],
}


def permissions_for(actions):
    selected = []
    for app_label, models in DIRECTORY_MODELS.items():
        codenames = [f"{action}_{model}" for model in models for action in actions]
        selected += Permission.objects.filter(
            content_type__app_label=app_label, codename__in=codenames
        )
    return selected


class Command(BaseCommand):
    help = "Create the Administrator and Ordinary user groups with their permissions."

    def handle(self, *args, **options):
        admin_group, _ = Group.objects.get_or_create(name=ADMIN_GROUP)
        user_group, _ = Group.objects.get_or_create(name=USER_GROUP)

        audit_view = Permission.objects.filter(
            content_type__app_label="audit", codename="view_auditlog"
        )
        admin_group.permissions.set(
            permissions_for(["add", "change", "delete", "view"]) + list(audit_view)
        )
        user_group.permissions.set(permissions_for(["view"]))

        self.stdout.write(self.style.SUCCESS("Roles are set up."))