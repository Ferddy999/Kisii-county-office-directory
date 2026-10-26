from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.urls import reverse

from core.factories import DirectoryTestCase, make_department, make_office, make_staff
from departments.models import Directorate

from .models import Office


class OfficeRuleTests(DirectoryTestCase):
    def test_extension_must_be_unique_within_a_building(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_office(self.department, name="Other Office", email="other@example.go.ke")

    def test_same_extension_is_fine_in_another_building(self):
        make_office(self.department, name="Other Office", email="other@example.go.ke", building="Block B")
        self.assertEqual(Office.objects.count(), 2)

    def test_blank_extensions_do_not_clash(self):
        make_office(self.department, name="Office One", email="one@example.go.ke", phone_ext="")
        make_office(self.department, name="Office Two", email="two@example.go.ke", phone_ext="")
        self.assertEqual(Office.objects.filter(phone_ext="").count(), 2)

    def test_office_name_must_be_unique_within_a_department(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_office(self.department, email="different@example.go.ke", phone_ext="999")

    def test_same_office_name_is_fine_in_another_department(self):
        other = make_department("Water and Environment", "WAT")
        make_office(other, email="water@example.go.ke", building="Block B", phone_ext="202")
        self.assertEqual(Office.objects.filter(name="Land Registry").count(), 2)

    def test_office_email_must_be_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            make_office(self.department, name="Other Office", building="Block B")

    def test_directorate_must_belong_to_the_same_department(self):
        other = make_department("Water and Environment", "WAT")
        directorate = Directorate.objects.create(department=other, name="Water Services")
        office = Office(name="Misfiled", department=self.department, directorate=directorate,
                        building="Block C", email="misfiled@example.go.ke")
        with self.assertRaises(ValidationError):
            office.full_clean()

    def test_department_with_offices_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.department.delete()

    def test_office_with_staff_cannot_be_deleted(self):
        make_staff(self.office)
        self.client.force_login(self.admin)
        self.client.post(reverse("office_delete", args=[self.office.pk]))
        self.assertTrue(Office.objects.filter(pk=self.office.pk).exists())

    def test_ordinary_user_cannot_add_an_office(self):
        self.client.force_login(self.viewer)
        response = self.client.post(reverse("office_add"), {"name": "Sneaky Office"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Office.objects.count(), 1)
