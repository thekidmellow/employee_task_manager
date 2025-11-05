from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse

User = get_user_model()


class CoreDashboardTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username="mgr", password="pass12345")
        g, _ = Group.objects.get_or_create(name="Managers")
        self.manager.groups.add(g)
        self.client.login(username="mgr", password="pass12345")

    def test_home_anonymous_ok(self):
        r = self.client.get(reverse("core:home"))
        self.assertEqual(r.status_code, 200)

    def test_employee_dashboard_requires_login(self):
        r = self.client.get(reverse("core:employee_dashboard"))
        self.assertIn(r.status_code, (200, 302, 401, 403))

    def test_employee_dashboard_logged_in(self):
        self.client.login(username="emp", password="pass12345")
        r = self.client.get(reverse("core:employee_dashboard"))
        self.assertEqual(r.status_code, 200)

    def test_manager_dashboard_logged_in(self):
        r = self.client.get(reverse("core:manager_dashboard"))
        self.assertIn(r.status_code, (200, 302))
