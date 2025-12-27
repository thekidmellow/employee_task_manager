from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


class AccountsViewCoverageTests(TestCase):
    def setUp(self):
        self.u = User.objects.create_user(username="u", password="pass12345")
        Group.objects.get_or_create(name="Managers")
        Group.objects.get_or_create(name="Employees")

    def test_login_get_and_invalid_post(self):
        url = reverse("accounts:login")
        self.assertEqual(self.client.get(url).status_code, 200)
        bad = self.client.post(
            url, data={"username": "u", "password": "wrong"})
        self.assertIn(bad.status_code, (200, 302))

    def test_profile_requires_login_then_ok(self):
        url = reverse("accounts:profile")
        self.assertIn(self.client.get(url).status_code, (302, 401, 403))
        self.client.login(username="u", password="pass12345")
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_register_get(self):
        self.assertEqual(self.client.get(
            reverse("accounts:register")).status_code, 200)

    def test_dashboard_redirect(self):
        self.client.login(username="u", password="pass12345")
        r = self.client.get(reverse("accounts:dashboard_redirect"))
        self.assertIn(r.status_code, (200, 302))
