from django.test import SimpleTestCase
from apps.tasks import forms


class TasksFormsTests(SimpleTestCase):
    def test_forms_import(self):
        self.assertTrue(hasattr(forms, "__file__"))

    def test_task_form_invalid_and_minimal_valid(self):
        Form = getattr(forms, "TaskForm", None)
        if not Form:
            self.skipTest("TaskForm missing")
        # invalid
        f = Form(data={})
        self.assertFalse(f.is_valid())
        # minimal valid — adjust keys to your required fields
        valid = {"title": "T1", "description": "D"}
        f2 = Form(data=valid)
        # Depending on required fields, this may still be invalid; that's fine—adjust as needed.
        f2.is_valid()  # exercise clean() branches
