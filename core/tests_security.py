from django.core import mail
from django.urls import reverse

from .factories import PASSWORD, DirectoryTestCase


class LoginThrottleTests(DirectoryTestCase):
    def attempt(self, password, username="viewer.test"):
        return self.client.post(reverse("login"), {
            "username": username, "password": password, "portal": "member"})

    def test_account_is_locked_after_five_wrong_passwords(self):
        for _ in range(5):
            self.attempt("wrong-password")
        response = self.attempt(PASSWORD)
        self.assertContains(response, "Too many failed attempts")
        self.assertEqual(len(mail.outbox), 0)

    def test_four_wrong_passwords_do_not_lock(self):
        for _ in range(4):
            self.attempt("wrong-password")
        response = self.attempt(PASSWORD)
        self.assertRedirects(response, reverse("login_verify"))

    def test_a_good_sign_in_resets_the_count(self):
        for _ in range(4):
            self.attempt("wrong-password")
        self.attempt(PASSWORD)
        for _ in range(4):
            self.attempt("wrong-password")
        response = self.attempt(PASSWORD)
        self.assertRedirects(response, reverse("login_verify"))

    def test_other_accounts_are_not_affected(self):
        for _ in range(5):
            self.attempt("wrong-password")
        response = self.attempt(PASSWORD, username="admin.test")
        self.assertRedirects(response, reverse("login_verify"))
