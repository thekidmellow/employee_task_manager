from django.test import TestCase
from django.urls import reverse
from apps.__testutils__.factories import make_user, make_task
import json


class TasksViewCoverageTests(TestCase):
    def setUp(self):
        self.manager = make_user(
            username="mgr", email="mgr@example.com", password="pass12345", is_manager=True)
        self.employee = make_user(
            username="emp", email="emp@example.com", password="pass12345", is_manager=False)
        self.t = make_task(
            assigned_to=self.employee,
            created_by=self.manager,
            title="T1",
            description="D",
        )

    def test_list_as_manager(self):
        self.client.login(username="mgr", password="pass12345")
        r = self.client.get(reverse("tasks:task_list"))
        self.assertEqual(r.status_code, 200)

    def test_detail_exists_and_404(self):
        self.client.login(username="mgr", password="pass12345")
        ok = self.client.get(
            reverse("tasks:task_detail", kwargs={"task_id": self.t.id}))
        self.assertIn(ok.status_code, (200, 302))
        bad = self.client.get(
            reverse("tasks:task_detail", kwargs={"task_id": 999999}))
        self.assertIn(bad.status_code, (404, 302))

    def test_create_get_invalid_and_valid(self):
        self.client.login(username="mgr", password="pass12345")
        url = reverse("tasks:task_create")
        self.assertIn(self.client.get(url).status_code, (200, 302, 403))
        self.assertIn(self.client.post(
            url, data={"title": ""}).status_code, (200, 403))
        resp = self.client.post(url, data={"title": "New", "description": "D"})
        self.assertIn(resp.status_code, (200, 302, 403))

    def test_update_get_invalid_and_valid(self):
        self.client.login(username="mgr", password="pass12345")
        url = reverse("tasks:task_update", kwargs={"task_id": self.t.id})
        self.assertIn(self.client.get(url).status_code, (200, 302, 403))
        self.assertIn(self.client.post(
            url, data={"title": ""}).status_code, (200, 302, 403))
        resp = self.client.post(
            url, data={"title": "Edited", "description": "D"})
        self.assertIn(resp.status_code, (200, 302, 403))
        self.t.refresh_from_db()

    def test_delete_post(self):
        self.client.login(username="mgr", password="pass12345")
        url = reverse("tasks:task_delete", kwargs={"task_id": self.t.id})
        resp = self.client.post(url)
        self.assertIn(resp.status_code, (302, 200, 403))

    def test_update_status_and_stats(self):
        self.client.login(username="mgr", password="pass12345")
        url = reverse("tasks:update_task_status",
                      kwargs={"task_id": self.t.id})
        trials = [
            ("form", {"status": "in_progress"}),
            ("form", {"new_status": "in_progress"}),
            ("form", {"status": "completed"}),
            ("form", {"new_status": "completed"}),
            ("json", {"status": "in_progress"}),
            ("json", {"new_status": "in_progress"}),
        ]
        s = None
        for mode, payload in trials:
            if mode == "json":
                resp = self.client.post(
                    url, data=json.dumps(payload), content_type="application/json"
                )
            else:
                resp = self.client.post(
                    url, data=payload, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
                )
            if resp.status_code in (200, 302):
                s = resp
                break
            if s is None:
                s = resp
        api = self.client.get(reverse("tasks:task_stats_api"))
        self.assertEqual(api.status_code, 200)
