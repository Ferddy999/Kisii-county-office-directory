if (-not (Test-Path "manage.py")) {
    Write-Host "Run this from the project root (the folder that contains manage.py)." -ForegroundColor Red
    exit 1
}
$utf8 = New-Object System.Text.UTF8Encoding $false

function Write-File($path, $content) {
    $full = Join-Path (Get-Location) $path
    $dir = Split-Path $full
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
    $text = $content.Trim("`r", "`n") + "`n"
    [System.IO.File]::WriteAllText($full, $text, $utf8)
    Write-Host "wrote $path"
}

function Patch-File($path, $old, $new, $marker) {
    $full = (Resolve-Path $path).Path
    $t = [System.IO.File]::ReadAllText($full)
    if ($t.Contains($marker)) { Write-Host "skip $path (already patched)"; return }
    if (-not $t.Contains($old)) { Write-Host "WARNING: expected text not found in $path" -ForegroundColor Yellow; return }
    [System.IO.File]::WriteAllText($full, $t.Replace($old, $new.Trim()), $utf8)
    Write-Host "patched $path"
}

Write-File "audit\context.py" @'
from contextvars import ContextVar

# The signed-in user for the request being handled (None outside a request).
current_user = ContextVar("audit_current_user", default=None)
'@

Write-File "audit\middleware.py" @'
from .context import current_user


class AuditUserMiddleware:
    """Remember who is making the request so signals can record it."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = current_user.set(getattr(request, "user", None))
        try:
            return self.get_response(request)
        finally:
            current_user.reset(token)
'@

Write-File "audit\signals.py" @'
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_delete, post_save, pre_save

from .context import current_user
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
'@

Write-File "audit\apps.py" @'
from django.apps import AppConfig


class AuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "audit"

    def ready(self):
        from .signals import connect

        connect()
'@

Write-File "audit\views.py" @'
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import ListView

from .models import AuditLog


class AuditLogList(PermissionRequiredMixin, ListView):
    model = AuditLog
    permission_required = "audit.view_auditlog"
    raise_exception = True
    paginate_by = 15
'@

Write-File "audit\urls.py" @'
from django.urls import path

from . import views

urlpatterns = [
    path("", views.AuditLogList.as_view(), name="audit_log"),
]
'@

Write-File "templates\audit\auditlog_list.html" @'
{% extends "base.html" %}

{% block title %}Audit log{% endblock %}

{% block content %}
<div>
  <h1 class="page-title">Audit log</h1>
  <div class="page-subtitle">Every change made by a signed-in administrator. {{ paginator.count }} entr{{ paginator.count|pluralize:"y,ies" }}.</div>
</div>

<section class="panel">
  <div class="result-row audit-cols head">
    <div>When</div><div>User</div><div>Action</div><div>Record</div><div>Details</div>
  </div>
  {% for entry in object_list %}
  <div class="result-row audit-cols">
    <div>{{ entry.created_at|date:"j M Y, H:i" }}</div>
    <div>{{ entry.username|default:"unknown" }}</div>
    <div><span class="status action-{{ entry.action }}">{{ entry.get_action_display }}</span></div>
    <div>
      <div class="strong">{{ entry.object_repr }}</div>
      <div class="sub">{{ entry.model_name|capfirst }}</div>
    </div>
    <div>
      {% for field, change in entry.changes.items %}
      <div class="sub"><strong>{{ field }}</strong>:
        {% if entry.action == "update" %}{{ change.from|default_if_none:"-" }} &rarr; {{ change.to|default_if_none:"-" }}
        {% elif entry.action == "create" %}{{ change.to|default_if_none:"-" }}
        {% else %}{{ change.from|default_if_none:"-" }}{% endif %}
      </div>
      {% endfor %}
    </div>
  </div>
  {% empty %}
  <div class="empty">No changes recorded yet.</div>
  {% endfor %}
  {% if is_paginated %}
  <nav class="pagination" aria-label="Pagination">
    <div class="pages">
      {% if page_obj.has_previous %}<a class="page" href="?page={{ page_obj.previous_page_number }}">Prev</a>{% endif %}
      <span class="page current" aria-current="page">{{ page_obj.number }}</span>
      <span class="result-count">of {{ paginator.num_pages }}</span>
      {% if page_obj.has_next %}<a class="page" href="?page={{ page_obj.next_page_number }}">Next</a>{% endif %}
    </div>
  </nav>
  {% endif %}
</section>
{% endblock %}
'@

$mw = @'
'django.contrib.auth.middleware.LoginRequiredMiddleware',
    'audit.middleware.AuditUserMiddleware',
'@
Patch-File "config\settings.py" "'django.contrib.auth.middleware.LoginRequiredMiddleware'," $mw "AuditUserMiddleware"

$urlsNew = @'
path('audit/', include('audit.urls')),
    path('departments/', include('departments.urls')),
'@
Patch-File "config\urls.py" "path('departments/', include('departments.urls'))," $urlsNew "audit.urls"

$navNew = @'
<a href="{% url 'audit_log' %}" {% if request.path|slice:":7" == "/audit/" %}class="active"{% endif %}>Audit log</a>
'@
Patch-File "templates\partials\header.html" '<a href="#">Audit log</a>' $navNew "audit_log"

$dashNew = @'
<a href="{% url 'audit_log' %}">View all</a>
'@
Patch-File "templates\core\dashboard.html" '<span class="panel-note">Administrator only</span>' $dashNew "audit_log"

$cp = (Resolve-Path "static\css\site.css").Path
$c = [System.IO.File]::ReadAllText($cp)
if ($c.Contains(".audit-cols")) {
    Write-Host "site.css already has the audit styles, skipping."
} else {
    $more = @'


/* audit log */
.audit-cols { grid-template-columns: 150px 110px 90px minmax(0, 1.2fr) minmax(0, 2fr); }
.status.action-update { background: var(--blue-tint); color: var(--blue-dark); }
.status.action-delete { background: #FCEBEB; color: #8A1F1F; }

@media (max-width: 720px) {
  .audit-cols { grid-template-columns: 1fr; gap: 4px; }
}
'@
    [System.IO.File]::WriteAllText($cp, $c.TrimEnd() + "`n" + $more.TrimEnd() + "`n", $utf8)
    Write-Host "appended audit styles to static\css\site.css"
}

Write-Host ""
Write-Host "Checking..."
$checks = [ordered]@{
  "signals"          = @("audit\signals.py", 'def connect')
  "middleware"       = @("audit\middleware.py", 'class AuditUserMiddleware')
  "app config"       = @("audit\apps.py", 'def ready')
  "audit view"       = @("audit\views.py", 'class AuditLogList')
  "audit template"   = @("templates\audit\auditlog_list.html", 'audit-cols')
  "middleware set"   = @("config\settings.py", 'audit.middleware.AuditUserMiddleware')
  "audit url"        = @("config\urls.py", 'audit.urls')
  "nav link"         = @("templates\partials\header.html", "url 'audit_log'")
  "dashboard link"   = @("templates\core\dashboard.html", "url 'audit_log'")
  "audit css"        = @("static\css\site.css", '.audit-cols')
}
foreach ($k in $checks.Keys) {
  $f, $p = $checks[$k]
  $ok = (Test-Path $f) -and (Select-String -Path $f -Pattern $p -SimpleMatch -Quiet)
  "{0,-18} {1}" -f $k, $(if ($ok) { "OK" } else { "MISSING" })
}
Write-Host ""
python manage.py check