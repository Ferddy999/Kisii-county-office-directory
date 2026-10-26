from django.urls import reverse

from core.factories import DirectoryTestCase, make_department, make_office, make_staff

from .forms import StaffForm
from .models import Staff


def staff_data(test, **extra):
    data = {
        "full_name": "  Brian   Otieno ",
        "designation": "Officer",
        "department": test.department.pk,
        "office": test.office.pk,
        "work_email": "Brian.Otieno@Example.go.ke",
        "work_phone": "0712 345 678",
        "is_active": "on",
    }
    data.update(extra)
    return data


class StaffFormTests(DirectoryTestCase):
    def test_input_is_cleaned_and_normalised(self):
        form = StaffForm(staff_data(self))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["full_name"], "Brian Otieno")
        self.assertEqual(form.cleaned_data["work_email"], "brian.otieno@example.go.ke")
        self.assertEqual(form.cleaned_data["work_phone"], "+254712345678")

    def test_international_phone_format_is_accepted(self):
        form = StaffForm(staff_data(self, work_phone="+254 712 345 678"))
        self.assertTrue(form.is_valid(), form.errors)

    def test_bad_phone_is_refused(self):
        for bad in ["12345", "0712", "abc", "+255712345678"]:
            with self.subTest(phone=bad):
                form = StaffForm(staff_data(self, work_phone=bad))
                self.assertFalse(form.is_valid())
                self.assertIn("work_phone", form.errors)

    def test_bad_email_is_refused(self):
        form = StaffForm(staff_data(self, work_email="not-an-email"))
        self.assertIn("work_email", form.errors)

    def test_duplicate_email_is_refused_whatever_the_case(self):
        make_staff(self.office, email="brian.otieno@example.go.ke", phone="+254799999999")
        form = StaffForm(staff_data(self))
        self.assertFalse(form.is_valid())
        self.assertIn("work_email", form.errors)

    def test_duplicate_phone_is_refused_in_any_format(self):
        make_staff(self.office, email="other@example.go.ke", phone="+254712345678")
        form = StaffForm(staff_data(self))
        self.assertFalse(form.is_valid())
        self.assertIn("work_phone", form.errors)

    def test_office_must_belong_to_the_department(self):
        water = make_department("Water and Environment", "WAT")
        water_office = make_office(water, name="Water Office", email="water@example.go.ke",
                                   building="Block B", phone_ext="202")
        form = StaffForm(staff_data(self, office=water_office.pk))
        self.assertFalse(form.is_valid())
        self.assertIn("office", form.errors)

    def test_required_fields(self):
        form = StaffForm({})
        for field in ["full_name", "designation", "department", "office", "work_email", "work_phone"]:
            with self.subTest(field=field):
                self.assertIn(field, form.errors)


class StaffViewTests(DirectoryTestCase):
    def test_administrator_can_add_staff(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("staff_add"), staff_data(self))
        self.assertRedirects(response, reverse("staff_list"))
        self.assertTrue(Staff.objects.filter(work_email="brian.otieno@example.go.ke").exists())

    def test_invalid_form_is_shown_again_and_saves_nothing(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("staff_add"), staff_data(self, work_phone="12345"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Staff.objects.count(), 0)

    def test_ordinary_user_cannot_add_staff(self):
        self.client.force_login(self.viewer)
        response = self.client.post(reverse("staff_add"), staff_data(self))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Staff.objects.count(), 0)

    def test_administrator_can_edit_and_delete(self):
        staff = make_staff(self.office)
        self.client.force_login(self.admin)
        self.client.post(reverse("staff_edit", args=[staff.pk]),
                         staff_data(self, full_name="Alice W", work_email="alice@example.go.ke",
                                    work_phone="0711111111"))
        staff.refresh_from_db()
        self.assertEqual(staff.full_name, "Alice W")
        self.client.post(reverse("staff_delete", args=[staff.pk]))
        self.assertFalse(Staff.objects.filter(pk=staff.pk).exists())
