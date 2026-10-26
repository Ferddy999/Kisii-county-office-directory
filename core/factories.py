"""Shared helpers for the test suite."""
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from departments.models import Department
from offices.models import Office
from staff.models import Staff

from .legal import TERMS_VERSION
from .models import ConsentLog
from .roles import ADMIN_GROUP, USER_GROUP

User = get_user_model()
PASSWORD = "Str0ng-Test-Pass!"


def make_user(username, group, email="", accepted_terms=True):
    user = User.objects.create_user(username, email=email, password=PASSWORD)
    user.groups.add(Group.objects.get(name=group))
    if accepted_terms:
        ConsentLog.objects.create(
            user=user, username=username, kind=ConsentLog.TERMS,
            version=TERMS_VERSION, choice="accepted",
        )
    return user


def make_department(name="Lands, Physical Planning", code="LND"):
    return Department.objects.create(name=name, code=code)


def make_office(department, name="Land Registry", email="registry@example.go.ke",
                building="Block A", phone_ext="101"):
    return Office.objects.create(
        name=name, department=department, building=building,
        email=email, phone_ext=phone_ext,
    )


def make_staff(office, name="Alice Wanjiru", email="alice@example.go.ke", phone="+254711111111"):
    return Staff.objects.create(
        full_name=name, designation="Clerk", department=office.department,
        office=office, work_email=email, work_phone=phone,
    )


class DirectoryTestCase(TestCase):
    """Roles, two users, one department and one office for every test."""

    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", stdout=StringIO())
        cls.admin = make_user("admin.test", ADMIN_GROUP, "admin.test@example.go.ke")
        cls.viewer = make_user("viewer.test", USER_GROUP, "viewer.test@example.go.ke")
        cls.department = make_department()
        cls.office = make_office(cls.department)
