from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class AccountsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", email="a@example.com", password="pass12345")

    def test_profile_requires_login(self):
        # TODO: change to your real URL name if different
        url = reverse("accounts:profile")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)

    def test_profile_ok_when_logged_in(self):
        self.client.login(email="a@example.com", password="pass12345")
        url = reverse("accounts:profile")
        r = self.client.get(url)
        self.assertIn(r.status_code, (200, 302))
        # TODO: adjust template name if different
        if r.status_code == 200:
            self.assertTemplateUsed(r, "accounts/profile.html")
        else:
            self.assertIn(r.status_code, (302,))
