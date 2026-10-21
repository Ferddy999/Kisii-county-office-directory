from django.contrib import admin

from .models import Staff


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("full_name", "designation", "department", "office", "work_phone", "work_email")
    list_filter = ("department", "is_active")
    list_select_related = ("department", "office")
    search_fields = ("full_name", "work_email", "work_phone")