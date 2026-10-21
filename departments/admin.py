from django.contrib import admin

from .models import Department, Directorate


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(Directorate)
class DirectorateAdmin(admin.ModelAdmin):
    list_display = ("name", "department")
    list_filter = ("department",)
    list_select_related = ("department",)
    search_fields = ("name",)