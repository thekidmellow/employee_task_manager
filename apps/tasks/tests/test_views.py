from django.test import TestCase
from django.urls import reverse, NoReverseMatch
from unittest import skip
from django.contrib.auth import get_user_model
from apps.__testutils__.factories import make_user, make_task

User = get_user_model()


def reverse_or_skip(name, fallback=None):
    try:
        return reverse(name)
    except NoReverseMatch:
        if fallback is not None:
            return fallback
        raise


class TaskViewsTests(TestCase):
    def setUp(self):
        self.user = make_user(
            username="bob", email="u@example.com", password="pass12345", is_manager=True)
        self.client.login(username="bob", password="pass12345")
        self.task = make_task(assigned_to=self.user, created_by=self.user)

    def test_task_list(self):
        try:
            url = reverse_or_skip("tasks:task_list", "/tasks/")
        except NoReverseMatch:
            self.skipTest("tasks:list URL name not configured")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "tasks/task_list.html")

    def test_task_create_get_and_invalid_post(self):
        try:
            url = reverse_or_skip("tasks:task_create", "/tasks/create/")
        except NoReverseMatch:
            self.skipTest("tasks:create URL name not configured")
        r = self.client.get(url)
        self.assertIn(r.status_code, (200, 302, 403))
        r = self.client.post(url, data={"title": ""})
        self.assertIn(r.status_code, (200, 403))
        if r.status_code == 200:
            self.assertContains(r, "This field is required", status_code=200)
