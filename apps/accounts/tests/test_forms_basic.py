from django.test import SimpleTestCase
from apps.accounts import forms


class AccountsFormsTests(SimpleTestCase):
    def test_imports(self):
        self.assertTrue(hasattr(forms, "__file__"))

    def test_example_form_invalid(self):
        # Replace ExampleForm with a real form from apps/accounts/forms.py
        Form = getattr(forms, "SignupForm", None) or getattr(
            forms, "ProfileForm", None)
        if not Form:
            self.skipTest("No target form found to test")
        f = Form(data={})  # empty -> invalid
        self.assertFalse(f.is_valid())
