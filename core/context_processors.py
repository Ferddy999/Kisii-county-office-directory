from .roles import is_administrator


def role(request):
    user = request.user
    if not user.is_authenticated:
        return {}
    admin = is_administrator(user)
    return {
        "is_administrator": admin,
        "role_label": "Administrator" if admin else "Ordinary user",
    }
