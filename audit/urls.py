from django.urls import path

from . import views

urlpatterns = [
    path("", views.AuditLogList.as_view(), name="audit_log"),
]
