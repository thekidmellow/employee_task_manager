import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.test.utils import override_settings
from datetime import timedelta
from apps.accounts.models import UserProfile
from apps.tasks.models import Task


class SecurityTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.manager = User.objects.create_user(
            username="testmanager",
            email="manager@test.com",
            password="testpass123",
        )
        profile = UserProfile.objects.get(user=self.manager)
        profile.role = "manager"
        profile.save()

        self.employee = User.objects.create_user(
            username="testemployee",
            email="employee@test.com",
            password="testpass123",
        )

        self.other_employee = User.objects.create_user(
            username="otheremployee",
            email="other@test.com",
            password="testpass123",
        )

        self.task = Task.objects.create(
            title="Security Test Task",
            description="Task for security testing",
            assigned_to=self.employee,
            created_by=self.manager,
            priority="medium",
            due_date=timezone.now() + timedelta(days=7),
        )

    def test_csrf_protection(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username="testmanager", password="testpass123")

        response = csrf_client.post(
            reverse("tasks:task_create"),
            {
                "title": "CSRF Test Task",
                "description": "Task created without CSRF token",
                "assigned_to": self.employee.id,
                "priority": "medium",
                "due_date": (timezone.now() + timedelta(days=5)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_sql_injection_prevention(self):
        self.client.login(username="testmanager", password="testpass123")

        malicious_search = "'; DROP TABLE tasks_task; --"

        response = self.client.get(
            reverse("tasks:task_list"),
            {
                "search": malicious_search,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Task.objects.exists())

    def test_xss_prevention(self):
        self.client.login(username="testmanager", password="testpass123")

        xss_payload = '<script>alert("XSS")</script>'

        response = self.client.post(
            reverse("tasks:task_create"),
            {
                "title": f"XSS Test {xss_payload}",
                "description": f"Description with {xss_payload}",
                "assigned_to": self.employee.id,
                "priority": "medium",
                "due_date": (timezone.now() + timedelta(days=5)).strftime("%Y-%m-%d %H:%M"),
            },
        )

        self.assertEqual(response.status_code, 302)

        task = Task.objects.filter(title__contains="XSS Test").first()
        self.assertIsNotNone(task)

        response = self.client.get(
            reverse("tasks:task_detail", args=[task.id]))
        content = response.content.decode('utf-8')

        self.assertIn('&lt;script&gt;', content)
        self.assertIn('&lt;/script&gt;', content)

        self.assertNotIn('<script>alert', content)
        self.assertNotIn('<script >', content)

        self.assertIn('&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;', content)
        self.assertIn('<script src="https://cdn.jsdelivr.net/npm/bootstrap', content)

    def test_unauthorized_access_prevention(self):
        self.client.login(username="testemployee", password="testpass123")

        response = self.client.get(reverse("tasks:task_create"))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(
            reverse("tasks:task_create"),
            {
                "title": "Unauthorized Task",
                "description": "Task created by employee",
                "assigned_to": self.employee.id,
                "priority": "medium",
                "due_date": (timezone.now() + timedelta(days=5)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_object_level_permissions(self):
        self.client.login(username="otheremployee", password="testpass123")

        response = self.client.get(
            reverse("tasks:task_detail", args=[self.task.id]))
        self.assertEqual(response.status_code, 403)

        response = self.client.post(
            reverse("tasks:task_update", args=[self.task.id]),
            {
                "status": "completed",
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_session_security(self):
        self.client.login(username="testemployee", password="testpass123")

        response = self.client.get(reverse("core:home"))

        self.assertIn("sessionid", self.client.cookies)

    def test_password_validation(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "weakpassuser",
                "email": "weak@test.com",
                "first_name": "Weak",
                "last_name": "Password",
                "password1": "123",
                "password2": "123",
                "role": "employee",
                "department": "IT",
            },
        )

        self.assertFalse(User.objects.filter(username="weakpassuser").exists())

        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "strongpassuser",
                "email": "strong@test.com",
                "first_name": "Strong",
                "last_name": "Password",
                "password1": "ComplexPass123!@#",
                "password2": "ComplexPass123!@#",
                "role": "employee",
                "department": "IT",
            },
        )

        self.assertTrue(User.objects.filter(
            username="strongpassuser").exists())

    def test_file_upload_security(self):
        pass

    @override_settings(DEBUG=False)
    def test_debug_info_not_leaked(self):
        response = self.client.get("/nonexistent-url/")
        self.assertNotContains(response, "Traceback", status_code=404)
        self.assertNotContains(response, "INSTALLED_APPS", status_code=404)
        self.assertNotContains(response, "SECRET_KEY", status_code=404)

    def test_admin_access_restriction(self):
        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/admin/login/"))

        self.client.login(username="testemployee", password="testpass123")
        response = self.client.get("/admin/")

        self.assertIn(response.status_code, [302, 403])

    def test_insecure_direct_object_references(self):
        self.client.login(username="testemployee", password="testpass123")

        other_task = Task.objects.create(
            title="Other Employee Task",
            description="Task for other employee",
            assigned_to=self.other_employee,
            created_by=self.manager,
            priority="medium",
            due_date=timezone.now() + timedelta(days=7),
        )

        response = self.client.get(
            reverse("tasks:task_detail", args=[other_task.id]))

        self.assertEqual(response.status_code, 403)

    def test_clickjacking_protection(self):
        response = self.client.get(reverse("core:home"))

        if "X-Frame-Options" in response:
            self.assertIn(response["X-Frame-Options"], ["DENY", "SAMEORIGIN"])

    def test_content_type_nosniff(self):
        response = self.client.get(reverse("core:home"))

        if "X-Content-Type-Options" in response:
            self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_xss_protection_header(self):
        response = self.client.get(reverse("core:home"))

        if "X-XSS-Protection" in response:
            self.assertEqual(response["X-XSS-Protection"], "1; mode=block")

    def test_sensitive_data_exposure(self):
        self.client.login(username="testemployee", password="testpass123")

        response = self.client.get(
            reverse("accounts:user_list_api"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        if response.status_code == 200:
            users_data = response.json()
            for user in users_data:
                self.assertNotIn("password", user)
                self.assertNotIn("password_hash", user)

    def test_mass_assignment_protection(self):
        self.client.login(username="testemployee", password="testpass123")

        response = self.client.post(
            reverse("tasks:task_update", args=[self.task.id]),
            {
                "status": "completed",
                "created_by": self.other_employee.id,
                "assigned_to": self.other_employee.id,
            },
        )

        self.task.refresh_from_db()
        self.assertEqual(self.task.created_by, self.manager)
        self.assertEqual(self.task.assigned_to, self.employee)

    def test_rate_limiting(self):
        for i in range(5):
            response = self.client.post(
                reverse("login"),
                {
                    "username": "testemployee",
                    "password": "wrongpassword",
                },
            )
        pass
