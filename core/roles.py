ADMIN_GROUP = "Administrator"
USER_GROUP = "Ordinary user"


def is_administrator(user):
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name=ADMIN_GROUP).exists()
