from django.contrib import admin

from .models import Office, Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "building", "phone_ext", "email", "is_active")
    list_filter = ("department", "is_active")
    list_select_related = ("department",)
    search_fields = ("name", "building", "email")
    filter_horizontal = ("services",)