from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import UserProfile
from .forms import UserRegistrationForm, UserProfileForm


class UserProfileModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )

    def test_user_profile_creation(self):

        self.assertTrue(hasattr(self.user, "userprofile"))
        self.assertEqual(self.user.userprofile.role, "employee")

    def test_is_manager_property(self):

        self.assertFalse(self.user.userprofile.is_manager)
        self.user.userprofile.role = "manager"
        self.user.userprofile.save()
        self.assertTrue(self.user.userprofile.is_manager)

    def test_is_employee_property(self):

        self.assertTrue(self.user.userprofile.is_employee)
        self.user.userprofile.role = "manager"
        self.user.userprofile.save()
        self.assertFalse(self.user.userprofile.is_employee)


class UserRegistrationFormTest(TestCase):

    def test_valid_form(self):

        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password1": "complexpass123",
            "password2": "complexpass123",
            "role": "employee",
            "department": "IT",
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_duplicate_email(self):

        User.objects.create_user(
            username="existing",
            email="existing@example.com",
        )
        form_data = {
            "username": "newuser",
            "email": "existing@example.com",
            "first_name": "New",
            "last_name": "User",
            "password1": "complexpass123",
            "password2": "complexpass123",
            "role": "employee",
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class AccountsViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )

    def test_register_view_get(self):

        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Register")

    def test_login_view_get(self):

        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login")

    def test_profile_view_authenticated(self):

        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)

    def test_profile_view_unauthenticated(self):

        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)
