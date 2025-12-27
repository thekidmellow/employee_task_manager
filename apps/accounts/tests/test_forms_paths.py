from django.test import SimpleTestCase
from apps.accounts import forms


class AccountFormPathsTests(SimpleTestCase):
    def test_signup_or_profile_form_paths(self):
        Candidate = getattr(forms, "SignupForm", None) or getattr(
            forms, "ProfileForm", None)
        if not Candidate:
            self.skipTest("SignupForm/ProfileForm not found")
        f = Candidate(data={})
        self.assertFalse(f.is_valid())
        # Try a minimal valid shape if you know required fields, e.g.:
        # f2 = Candidate(data={...}); f2.is_valid()
