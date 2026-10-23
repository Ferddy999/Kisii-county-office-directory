from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_delete, post_save, pre_save

from .context import current_user, suppressed
from .models import AuditLog

AUDITED = [
    "departments.Department",
    "departments.Directorate",
    "offices.Office",
    "offices.Service",
    "staff.Staff",
]
SKIPPED_FIELDS = {"id", "created_at", "updated_at"}
LABELS = {"staff": "staff member"}


def snapshot(instance):
    """Readable field values for one record (related records shown by name)."""
    data = {}
    for field in instance._meta.concrete_fields:
        if field.name in SKIPPED_FIELDS:
            continue
        label = str(field.verbose_name).capitalize()
        if field.is_relation:
            try:
                related = getattr(instance, field.name)
            except ObjectDoesNotExist:
                related = None
            data[label] = str(related) if related is not None else None
        else:
            value = getattr(instance, field.attname)
            if value is None or isinstance(value, (str, int, float, bool)):
                data[label] = value
            else:
                data[label] = str(value)
    return data


def acting_user():
    if suppressed.get():
        return None
    user = current_user.get()
    if user is not None and user.is_authenticated:
        return user
    return None


def record(action, instance, before, after):
    user = acting_user()
    if user is None:
        return
    changes = {}
    for key in {**before, **after}:
        if before.get(key) != after.get(key):
            changes[key] = {"from": before.get(key), "to": after.get(key)}
    if action == "update" and not changes:
        return
    meta = instance._meta
    AuditLog.objects.create(
        user=user,
        username=user.get_username(),
        action=action,
        model_name=str(LABELS.get(meta.model_name, meta.verbose_name)),
        object_id=instance.pk,
        object_repr=str(instance)[:255],
        changes=changes,
    )


def remember_previous(sender, instance, **kwargs):
    instance._audit_before = {}
    if instance.pk is None or acting_user() is None:
        return
    previous = sender.objects.filter(pk=instance.pk).first()
    if previous is not None:
        instance._audit_before = snapshot(previous)


def log_save(sender, instance, created, raw=False, **kwargs):
    if raw or acting_user() is None:
        return
    before = {} if created else getattr(instance, "_audit_before", {})
    record("create" if created else "update", instance, before, snapshot(instance))


def log_delete(sender, instance, **kwargs):
    if acting_user() is None:
        return
    record("delete", instance, snapshot(instance), {})


def connect():
    for label in AUDITED:
        model = apps.get_model(label)
        pre_save.connect(remember_previous, sender=model, dispatch_uid=f"audit_pre_{label}")
        post_save.connect(log_save, sender=model, dispatch_uid=f"audit_save_{label}")
        post_delete.connect(log_delete, sender=model, dispatch_uid=f"audit_delete_{label}")
