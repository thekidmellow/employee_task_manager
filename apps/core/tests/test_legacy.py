from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class CoreViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="testpass123",
        )
        self.manager.userprofile.role = "manager"
        self.manager.userprofile.save()

    def test_home_view(self):

        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Employee Task Manager")

    def test_employee_dashboard_authenticated(self):

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("core:employee_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_manager_dashboard_authenticated(self):

        self.client.login(username="manager", password="testpass123")
        response = self.client.get(reverse("core:manager_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_redirect_employee(self):

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_redirect_manager(self):

        self.client.login(username="manager", password="testpass123")
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 302)
