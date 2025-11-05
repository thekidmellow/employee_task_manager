from django.test import SimpleTestCase
from django.urls import reverse, resolve

class CoreUrlsTests(SimpleTestCase):
    def test_core_urls_reverse_and_resolve(self):
        names = [
            "core:home",
            "core:dashboard",
            "core:about",
            "core:contact",
            # add these if they exist in your core/urls.py:
            "core:manager_dashboard",
            "core:employee_dashboard",
        ]
        for name in names:
            with self.subTest(name=name):
                url = reverse(name)
                self.assertIsNotNone(resolve(url).func)

class AccountsUrlsTests(SimpleTestCase):
    def test_accounts_urls_reverse_and_resolve(self):
        names = [
            "accounts:login",
            "accounts:logout",
            "accounts:register",
            "accounts:profile",
            "accounts:password_change",
            "accounts:password_change_done",
            "accounts:delete_account",
            "accounts:check_username",
            "accounts:dashboard_redirect",
        ]
        for name in names:
            with self.subTest(name=name):
                url = reverse(name)
                self.assertIsNotNone(resolve(url).func)

class TasksUrlsTests(SimpleTestCase):
    def test_tasks_urls_reverse_and_resolve(self):
        # adjust if any of these aren’t in apps/tasks/urls.py
        names = [
            "tasks:task_list",
            "tasks:task_create",
            "tasks:task_stats_api",
        ]
        for name in names:
            with self.subTest(name=name):
                url = reverse(name)
                self.assertIsNotNone(resolve(url).func)
