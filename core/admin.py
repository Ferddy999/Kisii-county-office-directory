from django.contrib import admin

from .models import ConsentLog


@admin.register(ConsentLog)
class ConsentLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "username", "kind", "choice", "version")
    list_filter = ("kind", "choice")
    search_fields = ("username",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
