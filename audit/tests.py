from django.urls import reverse

from core.factories import DirectoryTestCase, make_staff
from staff.models import Staff

from .models import AuditLog


def staff_data(test, **extra):
    data = {
        "full_name": "Alice Wanjiru",
        "designation": "Clerk",
        "department": test.department.pk,
        "office": test.office.pk,
        "work_email": "alice@example.go.ke",
        "work_phone": "+254711111111",
        "is_active": "on",
    }
    data.update(extra)
    return data


class AuditTrailTests(DirectoryTestCase):
    def setUp(self):
        self.client.force_login(self.admin)

    def test_changes_made_outside_a_request_are_not_logged(self):
        make_staff(self.office)
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_creating_a_record_is_logged(self):
        self.client.post(reverse("staff_add"), staff_data(self))
        entry = AuditLog.objects.get()
        self.assertEqual(entry.action, "create")
        self.assertEqual(entry.username, "admin.test")
        self.assertEqual(entry.user, self.admin)
        self.assertEqual(entry.model_name, "staff member")
        self.assertEqual(entry.object_repr, "Alice Wanjiru")

    def test_an_update_records_old_and_new_values(self):
        staff = make_staff(self.office)
        self.client.post(reverse("staff_edit", args=[staff.pk]),
                         staff_data(self, designation="Senior Clerk"))
        entry = AuditLog.objects.get()
        self.assertEqual(entry.action, "update")
        self.assertEqual(entry.changes["Designation"], {"from": "Clerk", "to": "Senior Clerk"})

    def test_saving_without_changes_is_not_logged(self):
        staff = make_staff(self.office)
        self.client.post(reverse("staff_edit", args=[staff.pk]), staff_data(self))
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_deleting_a_record_is_logged(self):
        staff = make_staff(self.office)
        self.client.post(reverse("staff_delete", args=[staff.pk]))
        entry = AuditLog.objects.get()
        self.assertEqual(entry.action, "delete")
        self.assertEqual(entry.object_repr, "Alice Wanjiru")
        self.assertFalse(Staff.objects.filter(pk=staff.pk).exists())

    def test_refused_changes_leave_no_log(self):
        staff = make_staff(self.office)
        self.client.force_login(self.viewer)
        self.client.post(reverse("staff_delete", args=[staff.pk]))
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_log_is_kept_when_the_user_is_deleted(self):
        self.client.post(reverse("staff_add"), staff_data(self))
        self.admin.delete()
        entry = AuditLog.objects.get()
        self.assertIsNone(entry.user)
        self.assertEqual(entry.username, "admin.test")

    def test_only_administrators_can_read_the_log(self):
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(reverse("audit_log")).status_code, 403)
