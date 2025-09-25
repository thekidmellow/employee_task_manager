from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class ProjectConfigurationTests(TestCase):

    def test_settings_import(self):
        from django.conf import settings
        self.assertTrue(settings.DEBUG is not None)

    def test_url_configuration(self):
        from django.urls import resolve
        admin_url = reverse('admin:index')
        self.assertTrue(admin_url.startswith('/admin/'))

    def test_database_connection(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertTrue(user.id is not None)
        self.assertEqual(user.username, 'testuser')
