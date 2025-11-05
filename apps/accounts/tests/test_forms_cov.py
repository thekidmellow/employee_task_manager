from django.test import SimpleTestCase
from apps.accounts import forms


class AccountFormsCoverageTests(SimpleTestCase):
    def test_signup_or_profile_form(self):
        Candidate = getattr(forms, "SignupForm", None) or getattr(forms, "ProfileForm", None)
        if not Candidate:
            self.skipTest("No target form found")
        f = Candidate(data={})
        self.assertFalse(f.is_valid())
