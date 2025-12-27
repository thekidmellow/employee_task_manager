from django.test import SimpleTestCase
from apps.accounts import forms


class AccountsFormsSmokeTests(SimpleTestCase):
    def test_forms_import(self):
        # Just verifies forms module loads
        self.assertTrue(hasattr(forms, "__doc__"))
