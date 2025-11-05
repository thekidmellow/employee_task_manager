from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


class AccountsBasicViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="pass12345")
        Group.objects.get_or_create(name="Managers")
        Group.objects.get_or_create(name="Employees")

    def test_login_page_loads(self):
        r = self.client.get(reverse("accounts:login"))
        self.assertEqual(r.status_code, 200)

    def test_profile_requires_login(self):
        r = self.client.get(reverse("accounts:profile"))
        self.assertIn(r.status_code, (302, 401, 403))

    def test_profile_when_logged_in(self):
        self.client.login(username="u", password="pass12345")
        r = self.client.get(reverse("accounts:profile"))
        self.assertEqual(r.status_code, 200)

    def test_dashboard_redirect_logged_in(self):
        self.client.login(username="u", password="pass12345")
        r = self.client.get(reverse("accounts:dashboard_redirect"))
        self.assertIn(r.status_code, (302, 200))  # redirect to correct dashboard
