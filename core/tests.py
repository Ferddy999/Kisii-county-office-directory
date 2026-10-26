import re
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from django.urls import reverse

from audit.models import AuditLog
from offices.models import Office
from staff.models import Staff

from .factories import PASSWORD, DirectoryTestCase, make_staff, make_user
from .legal import COOKIE_NAME, TERMS_VERSION
from .models import ConsentLog, UserProfile
from .roles import USER_GROUP

User = get_user_model()


def code_from_mail(index=-1):
    return re.search(r"code is (\d{6})", mail.outbox[index].body).group(1)


def wrong_code(real):
    return "111111" if real == "000000" else "000000"


class AccessTests(DirectoryTestCase):
    def test_anonymous_visitors_are_sent_to_login(self):
        names = ["dashboard", "directory", "staff_list", "office_list",
                 "department_list", "audit_log", "account_settings"]
        for name in names:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response["Location"])

    def test_public_pages_open_without_login(self):
        for name in ["login", "terms", "privacy", "cookie_settings", "password_reset"]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_ordinary_user_can_search_the_directory(self):
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(reverse("directory")).status_code, 200)

    def test_ordinary_user_is_blocked_from_admin_pages(self):
        self.client.force_login(self.viewer)
        for name in ["staff_add", "office_add", "department_add", "audit_log", "handover"]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 403)

    def test_administrator_can_open_admin_pages(self):
        self.client.force_login(self.admin)
        for name in ["staff_add", "office_add", "department_add", "audit_log", "handover"]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_ordinary_user_cannot_delete_records(self):
        staff = make_staff(self.office)
        self.client.force_login(self.viewer)
        response = self.client.post(reverse("staff_delete", args=[staff.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Staff.objects.filter(pk=staff.pk).exists())


class LoginFlowTests(DirectoryTestCase):
    def sign_in(self, username, portal="member", password=PASSWORD, **extra):
        data = {"username": username, "password": password, "portal": portal, **extra}
        return self.client.post(reverse("login"), data)

    def verify(self, code):
        return self.client.post(reverse("login_verify"), {"code": code})

    def signed_in(self):
        return "_auth_user_id" in self.client.session

    def test_correct_password_sends_a_code_and_waits(self):
        response = self.sign_in("viewer.test")
        self.assertRedirects(response, reverse("login_verify"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["viewer.test@example.go.ke"])
        self.assertFalse(self.signed_in())

    def test_password_alone_does_not_open_pages(self):
        self.sign_in("viewer.test")
        response = self.client.get(reverse("directory"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_wrong_password_sends_nothing(self):
        response = self.sign_in("viewer.test", password="not-the-password")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(self.signed_in())

    def test_member_lands_on_directory(self):
        self.sign_in("viewer.test")
        response = self.verify(code_from_mail())
        self.assertRedirects(response, reverse("directory"), fetch_redirect_response=False)
        self.assertTrue(self.signed_in())

    def test_administrator_as_senior_lands_on_dashboard(self):
        self.sign_in("admin.test", portal="senior")
        response = self.verify(code_from_mail())
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)

    def test_administrator_as_member_lands_on_directory(self):
        self.sign_in("admin.test", portal="member")
        response = self.verify(code_from_mail())
        self.assertRedirects(response, reverse("directory"), fetch_redirect_response=False)

    def test_ordinary_user_cannot_choose_senior(self):
        response = self.sign_in("viewer.test", portal="senior")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "does not have senior officer access")
        self.assertEqual(len(mail.outbox), 0)

    def test_deep_link_is_honoured(self):
        self.sign_in("admin.test", next=reverse("staff_list"))
        response = self.verify(code_from_mail())
        self.assertRedirects(response, reverse("staff_list"), fetch_redirect_response=False)

    def test_wrong_code_is_refused(self):
        self.sign_in("viewer.test")
        response = self.verify(wrong_code(code_from_mail()))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not correct")
        self.assertFalse(self.signed_in())

    def test_five_wrong_codes_end_the_attempt(self):
        self.sign_in("viewer.test")
        real = code_from_mail()
        for _ in range(5):
            self.verify(wrong_code(real))
        response = self.verify(real)
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)
        self.assertFalse(self.signed_in())

    def test_expired_code_is_refused(self):
        self.sign_in("viewer.test")
        real = code_from_mail()
        session = self.client.session
        pending = session["pending_login"]
        pending["expires"] = 0
        session["pending_login"] = pending
        session.save()
        response = self.verify(real)
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)
        self.assertFalse(self.signed_in())

    def test_verify_page_needs_a_pending_sign_in(self):
        response = self.client.get(reverse("login_verify"))
        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)

    def test_new_code_cannot_be_requested_straight_away(self):
        self.sign_in("viewer.test")
        response = self.client.post(reverse("login_verify"), {"resend": "1"})
        self.assertContains(response, "Please wait")
        self.assertEqual(len(mail.outbox), 1)

    def test_account_without_contact_details_is_refused(self):
        make_user("no.contact", USER_GROUP, email="")
        response = self.sign_in("no.contact")
        self.assertContains(response, "No email address or phone number")
        self.assertEqual(len(mail.outbox), 0)

    def test_sms_is_used_when_chosen(self):
        UserProfile.objects.create(user=self.viewer, phone="+254711000000", otp_channel="sms")
        with mock.patch("core.otp.send_sms") as sms:
            self.sign_in("viewer.test")
        sms.assert_called_once()
        self.assertEqual(sms.call_args[0][0], "+254711000000")
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(OTP_REQUIRED=False)
    def test_code_step_can_be_switched_off(self):
        response = self.sign_in("viewer.test")
        self.assertRedirects(response, reverse("directory"), fetch_redirect_response=False)
        self.assertTrue(self.signed_in())


class TermsAndCookieTests(DirectoryTestCase):
    def test_terms_must_be_accepted_on_first_use(self):
        user = make_user("new.user", USER_GROUP, "new@example.go.ke", accepted_terms=False)
        self.client.force_login(user)
        response = self.client.get(reverse("directory"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accept_terms"), response["Location"])

    def test_accepting_terms_opens_the_system_and_is_recorded(self):
        user = make_user("new.user", USER_GROUP, "new@example.go.ke", accepted_terms=False)
        self.client.force_login(user)
        self.client.post(reverse("accept_terms"), {"agree": "1"})
        self.assertTrue(ConsentLog.objects.filter(
            user=user, kind="terms", version=TERMS_VERSION, choice="accepted").exists())
        self.assertEqual(self.client.get(reverse("directory")).status_code, 200)

    def test_terms_cannot_be_accepted_without_ticking(self):
        user = make_user("new.user", USER_GROUP, "new@example.go.ke", accepted_terms=False)
        self.client.force_login(user)
        response = self.client.post(reverse("accept_terms"), {})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ConsentLog.objects.filter(user=user, kind="terms").exists())

    def test_cookie_banner_shows_until_a_choice_is_made(self):
        self.assertContains(self.client.get(reverse("login")), "Cookies on this system")
        response = self.client.post(reverse("cookie_settings"), {"choice": "essential"})
        self.assertEqual(response.cookies[COOKIE_NAME].value, "essential")
        self.assertNotContains(self.client.get(reverse("login")), "Cookies on this system")

    def test_signed_in_cookie_choice_is_recorded(self):
        self.client.force_login(self.viewer)
        self.client.post(reverse("cookie_settings"), {"choice": "all"})
        self.assertTrue(ConsentLog.objects.filter(
            user=self.viewer, kind="cookies", choice="all").exists())


class AccountTests(DirectoryTestCase):
    def setUp(self):
        self.client.force_login(self.viewer)

    def details(self, **extra):
        data = {"first_name": "Vera", "last_name": "Tester",
                "email": "viewer.test@example.go.ke", "phone": "0712 345 678",
                "otp_channel": "email"}
        data.update(extra)
        return data

    def test_details_are_saved_and_phone_is_normalised(self):
        response = self.client.post(reverse("account_settings"), self.details())
        self.assertRedirects(response, reverse("account_settings"))
        self.assertEqual(UserProfile.objects.get(user=self.viewer).phone, "+254712345678")

    def test_bad_phone_is_refused(self):
        response = self.client.post(reverse("account_settings"), self.details(phone="12345"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(UserProfile.objects.filter(user=self.viewer).exclude(phone="").exists())

    def test_email_or_phone_is_required(self):
        response = self.client.post(reverse("account_settings"), self.details(email="", phone=""))
        self.assertContains(response, "at least an email address or a phone number")

    def test_sms_needs_a_phone_number(self):
        response = self.client.post(
            reverse("account_settings"), self.details(phone="", otp_channel="sms"))
        self.assertContains(response, "Add a phone number")

    def test_another_accounts_email_is_refused(self):
        response = self.client.post(
            reverse("account_settings"), self.details(email="admin.test@example.go.ke"))
        self.assertContains(response, "already uses this email")

    def test_password_can_be_changed(self):
        new_password = "Another-Str0ng-Pass!"
        response = self.client.post(reverse("password_change"), {
            "old_password": PASSWORD, "new_password1": new_password, "new_password2": new_password})
        self.assertRedirects(response, reverse("account_settings"))
        self.client.logout()
        self.assertTrue(self.client.login(username="viewer.test", password=new_password))

    def test_weak_password_is_refused(self):
        response = self.client.post(reverse("password_change"), {
            "old_password": PASSWORD, "new_password1": "12345678", "new_password2": "12345678"})
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        self.assertTrue(self.client.login(username="viewer.test", password=PASSWORD))


class HandoverTests(DirectoryTestCase):
    def setUp(self):
        self.client.force_login(self.admin)

    def run_cleanup(self, targets, password=PASSWORD, confirm="DELETE"):
        return self.client.post(reverse("handover"), {
            "targets": targets, "password": password, "confirm": confirm})

    def test_wrong_password_deletes_nothing(self):
        make_staff(self.office)
        response = self.run_cleanup(["staff"], password="wrong")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Staff.objects.count(), 1)

    def test_confirmation_word_is_required(self):
        make_staff(self.office)
        self.run_cleanup(["staff"], confirm="delete please")
        self.assertEqual(Staff.objects.count(), 1)

    def test_nothing_ticked_deletes_nothing(self):
        make_staff(self.office)
        response = self.run_cleanup([])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Staff.objects.count(), 1)

    def test_selected_data_is_deleted_and_logged_once(self):
        make_staff(self.office)
        make_staff(self.office, name="Peter Ondieki", email="peter@example.go.ke", phone="+254722222222")
        response = self.run_cleanup(["staff"])
        self.assertRedirects(response, reverse("account_settings"))
        self.assertEqual(Staff.objects.count(), 0)
        self.assertTrue(Office.objects.filter(pk=self.office.pk).exists())
        self.assertEqual(AuditLog.objects.count(), 1)
        self.assertEqual(AuditLog.objects.get().model_name, "handover cleanup")

    def test_offices_with_staff_are_protected(self):
        make_staff(self.office)
        response = self.run_cleanup(["offices"])
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Office.objects.filter(pk=self.office.pk).exists())
        self.assertEqual(Staff.objects.count(), 1)

    def test_other_users_can_be_removed_but_not_administrators(self):
        self.run_cleanup(["users"])
        self.assertFalse(User.objects.filter(username="viewer.test").exists())
        self.assertTrue(User.objects.filter(username="admin.test").exists())

    def test_ordinary_user_cannot_run_cleanup(self):
        make_staff(self.office)
        self.client.force_login(self.viewer)
        response = self.run_cleanup(["staff"])
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Staff.objects.count(), 1)


class DirectorySearchTests(DirectoryTestCase):
    def test_search_finds_a_staff_member_by_name(self):
        make_staff(self.office)
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("directory"), {"q": "Alice"})
        self.assertContains(response, "Alice Wanjiru")

    def test_search_hides_non_matches(self):
        make_staff(self.office)
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("directory"), {"q": "Zebediah"})
        self.assertNotContains(response, "Alice Wanjiru")

    def test_ordinary_user_is_told_it_is_view_only(self):
        self.client.force_login(self.viewer)
        self.assertContains(self.client.get(reverse("directory")), "view-only")
