if (-not (Test-Path "manage.py")) {
    Write-Host "Run this from the project root (the folder that contains manage.py)." -ForegroundColor Red
    exit 1
}

function Write-File($path, $content) {
    $full = Join-Path (Get-Location) $path
    $dir = Split-Path $full
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
    $text = $content.Trim("`r", "`n") + "`n"
    [System.IO.File]::WriteAllText($full, $text, (New-Object System.Text.UTF8Encoding $false))
    Write-Host "wrote $path"
}

Write-File "templates\registration\login.html" @'
{% extends "base.html" %}

{% block title %}Sign in{% endblock %}

{% block content %}
<div class="auth-card">
  <div>
    <h1 class="page-title">Sign in</h1>
    <div class="page-subtitle">Authorised county staff only.</div>
  </div>
  <form method="post" class="auth-form">
    {% csrf_token %}
    {% if form.non_field_errors %}
    <div class="form-error" role="alert">{{ form.non_field_errors.0 }}</div>
    {% endif %}
    <div class="field">
      <label for="{{ form.username.id_for_label }}">Username</label>
      {{ form.username }}
    </div>
    <div class="field">
      <label for="{{ form.password.id_for_label }}">Password</label>
      {{ form.password }}
    </div>
    <input type="hidden" name="next" value="{{ next }}">
    <button type="submit" class="btn-submit">Sign in</button>
  </form>
</div>
{% endblock %}
'@

Write-File "templates\partials\header.html" @'
<header class="site-header">
  <div class="container">
    <div class="brand">
      <div class="brand-mark">Logo</div>
      <div>
        <div class="brand-kicker">COUNTY GOVERNMENT OF KISII</div>
        <div class="brand-name">Office Directory</div>
      </div>
    </div>
    {% if user.is_authenticated %}
    <nav class="site-nav" aria-label="Main">
      <a href="{% url 'dashboard' %}" {% if request.resolver_match.url_name == 'dashboard' %}class="active"{% endif %}>Dashboard</a>
      <a href="#">Directory</a>
      <a href="#">Departments</a>
      <a href="#">Offices</a>
      <a href="#">Staff</a>
      {% if perms.audit.view_auditlog %}<a href="#">Audit log</a>{% endif %}
    </nav>
    <div class="userbar">
      <span class="role-pill {% if not is_administrator %}role-pill--user{% endif %}">{{ role_label }}</span>
      <span>{{ user.get_username }}</span>
      <form method="post" action="{% url 'logout' %}" class="logout-form">
        {% csrf_token %}
        <button type="submit" class="link-button">Sign out</button>
      </form>
    </div>
    {% endif %}
  </div>
</header>
'@

Write-File "templates\core\dashboard.html" @'
{% extends "base.html" %}

{% block title %}Dashboard{% endblock %}

{% block content %}
<div class="page-head">
  <div>
    <h1 class="page-title">Dashboard</h1>
    <div class="page-subtitle">Overview of departments, offices and directory entries.</div>
  </div>
  {% if perms.offices.add_office %}
  <div class="actions">
    <span class="actions-note">Administrator only</span>
    <a href="#" class="btn btn-outline">Add office</a>
    <a href="#" class="btn btn-primary">Add staff member</a>
  </div>
  {% endif %}
</div>

<form class="search-bar" action="#" method="get" role="search">
  <label for="q" class="sr-only">Search the directory</label>
  <input id="q" name="q" type="search" placeholder="Search by staff name, office, department, location or service">
  <button type="submit">Search</button>
</form>

<div class="stat-grid">
  {% for t in totals %}
  <div class="stat-card">
    <div class="stat-label">{{ t.label }}</div>
    <div class="stat-value">{{ t.value }}</div>
    <div class="stat-note">{{ t.note }}</div>
  </div>
  {% endfor %}
</div>

<div class="dash-columns">
  <section class="panel panel-main">
    <div class="panel-head">
      <h2 class="panel-title">Departments</h2>
      <a href="#">View all</a>
    </div>
    <div class="dept-row head">
      <div>Name</div><div class="num">Offices</div><div class="num">Staff</div>
    </div>
    {% for d in departments %}
    <div class="dept-row">
      <div>{{ d.name }}</div>
      <div class="num">{{ d.office_count }}</div>
      <div class="num">{{ d.staff_count }}</div>
    </div>
    {% empty %}
    <div class="empty">No departments yet. Run the seed command.</div>
    {% endfor %}
  </section>

  {% if perms.audit.view_auditlog %}
  <section class="panel panel-side">
    <div class="panel-head">
      <h2 class="panel-title">Recent changes</h2>
      <span class="panel-note">Administrator only</span>
    </div>
    {% for c in recent_changes %}
    <div class="change-row">
      <div class="change-what">{{ c.get_action_display }} {{ c.model_name }}: {{ c.object_repr }}</div>
      <div class="change-meta">{{ c.username|default:"system" }} &middot; {{ c.created_at|date:"D j M, H:i" }}</div>
    </div>
    {% empty %}
    <div class="empty">No changes recorded yet.</div>
    {% endfor %}
  </section>
  {% endif %}
</div>
{% endblock %}
'@

Write-File "core\views.py" @'
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
'@

Write-Host ""
Write-Host "Checking..."
$checks = [ordered]@{
  "login page exists"       = @("templates\registration\login.html", 'auth-card')
  "header shows role"       = @("templates\partials\header.html", 'role_label')
  "header audit link gated" = @("templates\partials\header.html", 'perms.audit.view_auditlog')
  "dashboard buttons gated" = @("templates\core\dashboard.html", 'perms.offices.add_office')
  "dashboard audit gated"   = @("templates\core\dashboard.html", 'perms.audit.view_auditlog')
  "view checks permission"  = @("core\views.py", 'has_perm')
  "roles module"            = @("core\roles.py", 'ADMIN_GROUP')
  "context processor"       = @("core\context_processors.py", 'def role')
  "setup_roles command"     = @("core\management\commands\setup_roles.py", 'class Command')
  "login url"               = @("core\urls.py", 'LoginView')
  "login middleware"        = @("config\settings.py", 'LoginRequiredMiddleware')
  "role in settings"        = @("config\settings.py", 'core.context_processors.role')
  "login css"               = @("static\css\site.css", 'auth-card')
}
foreach ($k in $checks.Keys) {
  $f, $p = $checks[$k]
  $ok = (Test-Path $f) -and (Select-String -Path $f -Pattern $p -SimpleMatch -Quiet)
  "{0,-26} {1}" -f $k, $(if ($ok) { "OK" } else { "MISSING" })
}
Write-Host ""
python manage.py check