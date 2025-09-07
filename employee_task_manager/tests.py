"""
Test configuration for the Employee Task Manager
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class ProjectConfigurationTests(TestCase):
    """Test basic project configuration"""
    
    def test_settings_import(self):
        """Test that settings can be imported"""
        from django.conf import settings
        self.assertTrue(settings.DEBUG is not None)
    
    def test_url_configuration(self):
        """Test that URL configuration is working"""
        from django.urls import resolve
        # Test that admin URLs are configured
        admin_url = reverse('admin:index')
        self.assertTrue(admin_url.startswith('/admin/'))
    
    def test_database_connection(self):
        """Test database connection"""
        # Create a test user to verify database connectivity
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertTrue(user.id is not None)
        self.assertEqual(user.username, 'testuser')