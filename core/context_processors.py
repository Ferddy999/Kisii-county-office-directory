from .roles import ADMIN_GROUP


def role(request):
    user = request.user
    if not user.is_authenticated:
        return {}
    is_admin = user.is_superuser or user.groups.filter(name=ADMIN_GROUP).exists()
    return {
        "is_administrator": is_admin,
        "role_label": "Administrator" if is_admin else "Ordinary user",
    }