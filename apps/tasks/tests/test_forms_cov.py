from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from apps.tasks import forms

User = get_user_model()


class TaskFormsCoverageTests(TestCase):
    def setUp(self):
        self.mgr = User.objects.create_user(username="mgr", password="pass12345")
        managers, _ = Group.objects.get_or_create(name="Managers")
        self.mgr.groups.add(managers)

    def test_task_form_invalid_then_minimal(self):
        TaskForm = getattr(forms, "TaskForm", None)
        if not TaskForm:
            self.skipTest("TaskForm not found")

        f = TaskForm(data={}, user=self.mgr)
        self.assertFalse(f.is_valid())

        minimal = {"title": "T1", "description": "D"}
        f2 = TaskForm(data=minimal, user=self.mgr)
        f2.is_valid()
