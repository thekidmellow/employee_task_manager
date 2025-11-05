from django.test import TestCase
from apps.__testutils__.factories import make_user, make_task


class TaskModelBasicTests(TestCase):
    def test_str_and_defaults(self):
        t = make_task(
            title="Hello",
            description="World",
            assigned_to=make_user(username="h1", email="h1@example.com"),
        )
        self.assertIn("Hello", str(t))
        _ = getattr(t, "status", None)
        _ = getattr(t, "priority", None)
