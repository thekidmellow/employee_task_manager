# tests.py - Comprehensive test suite (LO4.1, LO4.3)
"""
Test suite for Employee Task Manager
Tests cover models, views, forms, and authentication
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.models import UserProfile
from tasks.models import Task, TaskComment
from tasks.forms import TaskForm, TaskCommentForm
from accounts.forms import UserRegistrationForm
import json


class UserProfileModelTest(TestCase):
    """Test UserProfile model (LO4.1)"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_profile_creation(self):
        """Test UserProfile is created with User"""
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.role, 'employee')  # default role
    
    def test_is_manager_property(self):
        """Test is_manager property"""
        profile = self.user.userprofile
        self.assertFalse(profile.is_manager)
        
        profile.role = 'manager'
        profile.save()
        self.assertTrue(profile.is_manager)
    
    def test_get_role_display(self):
        """Test role display method"""
        profile = self.user.userprofile
        self.assertEqual(profile.get_role_display(), 'Employee')
        
        profile.role = 'manager'
        self.assertEqual(profile.get_role_display(), 'Manager')


class TaskModelTest(TestCase):
    """Test Task model (LO4.1)"""
    
    def setUp(self):
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='testpass123'
        )
        self.manager.userprofile.role = 'manager'
        self.manager.userprofile.save()
        
        self.employee = User.objects.create_user(
            username='employee',
            email='employee@example.com',
            password='testpass123'
        )
        
        self.task = Task.objects.create(
            title='Test Task',
            description='Test task description',
            assigned_to=self.employee,
            created_by=self.manager,
            priority='medium',
            due_date=timezone.now().date() + timedelta(days=7)
        )
    
    def test_task_creation(self):
        """Test task is created correctly"""
        self.assertEqual(self.task.title, 'Test Task')
        self.assertEqual(self.task.status, 'pending')  # default status
        self.assertEqual(self.task.assigned_to, self.employee)
        self.assertEqual(self.task.created_by, self.manager)
    
    def test_task_str_method(self):
        """Test task string representation"""
        expected_str = f"{self.task.title} - {self.employee.username}"
        self.assertEqual(str(self.task), expected_str)
    
    def test_is_overdue_property(self):
        """Test is_overdue property"""
        # Future task should not be overdue
        self.assertFalse(self.task.is_overdue)
        
        # Past task should be overdue if not completed
        self.task.due_date = timezone.now().date() - timedelta(days=1)
        self.task.save()
        self.assertTrue(self.task.is_overdue)
        
        # Completed task should not be overdue even if past due
        self.task.status = 'completed'
        self.task.save()
        self.assertFalse(self.task.is_overdue)
    
    def test_get_progress_percentage(self):
        """Test progress percentage calculation"""
        # Pending task should be 0%
        self.assertEqual(self.task.get_progress_percentage(), 0)
        
        # In progress task should be 50%
        self.task.status = 'in_progress'
        self.assertEqual(self.task.get_progress_percentage(), 50)
        
        # Completed task should be 100%
        self.task.status = 'completed'
        self.assertEqual(self.task.get_progress_percentage(), 100)
    
    def test_get_priority_color(self):
        """Test priority color mapping"""
        self.task.priority = 'high'
        self.assertEqual(self.task.get_priority_color(), 'danger')
        
        self.task.priority = 'medium'
        self.assertEqual(self.task.get_priority_color(), 'warning')
        
        self.task.priority = 'low'
        self.assertEqual(self.task.get_priority_color(), 'success')


class TaskCommentModelTest(TestCase):
    """Test TaskComment model (LO4.1)"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.task = Task.objects.create(
            title='Test Task',
            description='Test description',
            assigned_to=self.user,
            created_by=self.user,
            due_date=timezone.now().date() + timedelta(days=7)
        )
        
        self.comment = TaskComment.objects.create(
            task=self.task,
            author=self.user,
            content='Test comment'
        )
    
    def test_comment_creation(self):
        """Test comment is created correctly"""
        self.assertEqual(self.comment.task, self.task)
        self.assertEqual(self.comment.author, self.user)
        self.assertEqual(self.comment.content, 'Test comment')
    
    def test_comment_str_method(self):
        """Test comment string representation"""
        expected_str = f"Comment by {self.user.username} on {self.task.title}"
        self.assertEqual(str(self.comment), expected_str)


class AuthenticationViewTest(TestCase):
    """Test authentication views (LO4.1)"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_login_view_get(self):
        """Test login page loads correctly"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login to Your Account')
    
    def test_login_view_post_valid(self):
        """Test successful login"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
    
    def test_login_view_post_invalid(self):
        """Test failed login"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct username and password')
    
    def test_logout_view(self):
        """Test logout functionality"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Redirect after logout
    
    def test_registration_view_get(self):
        """Test registration page loads correctly"""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Your Account')
    
    def test_registration_view_post_valid(self):
        """Test successful registration"""
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'newpass123',
            'password2': 'newpass123',
            'role': 'employee',
            'department': 'IT'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after registration
        self.assertTrue(User.objects.filter(username='newuser').exists())


class TaskViewTest(TestCase):
    """Test task-related views (LO4.1)"""
    
    def setUp(self):
        self.client = Client()
        
        # Create manager user
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='testpass123'
        )
        self.manager.userprofile.role = 'manager'
        self.manager.userprofile.save()
        
        # Create employee user
        self.employee = User.objects.create_user(
            username='employee',
            email='employee@example.com',
            password='testpass123'
        )
        
        # Create test task
        self.task = Task.objects.create(
            title='Test Task',
            description='Test task description',
            assigned_to=self.employee,
            created_by=self.manager,
            priority='medium',
            due_date=timezone.now().date() + timedelta(days=7)
        )
    
    def test_task_list_view_authenticated(self):
        """Test task list view for authenticated users"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('tasks:task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Task')
    
    def test_task_list_view_unauthenticated(self):
        """Test task list view redirects unauthenticated users"""
        response = self.client.get(reverse('tasks:task_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_task_detail_view(self):
        """Test task detail view"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('tasks:task_detail', args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.task.title)
        self.assertContains(response, self.task.description)
    
    def test_task_create_view_manager(self):
        """Test task creation by manager"""
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('tasks:task_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create New Task')
    
    def test_task_create_view_employee_forbidden(self):
        """Test task creation forbidden for employees"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('tasks:task_create'))
        self.assertEqual(response.status_code, 403)  # Forbidden
    
    def test_task_create_post_valid(self):
        """Test successful task creation"""
        self.client.login(username='manager', password='testpass123')
        response = self.client.post(reverse('tasks:task_create'), {
            'title': 'New Test Task',
            'description': 'New task description',
            'assigned_to': self.employee.pk,
            'priority': 'high',
            'due_date': (timezone.now().date() + timedelta(days=5)).strftime('%Y-%m-%d'),
            'estimated_hours': 8
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(Task.objects.filter(title='New Test Task').exists())
    
    def test_task_edit_view_authorized(self):
        """Test task editing by authorized users"""
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('tasks:task_edit', args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Task')
    
    def test_task_status_update_ajax(self):
        """Test AJAX task status update"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.post(
            reverse('tasks:task_update_status', args=[self.task.pk]),
            json.dumps({'status': 'in_progress'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Check task status was updated
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'in_progress')


class TaskFormTest(TestCase):
    """Test task forms (LO4.1)"""
    
    def setUp(self):
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='testpass123'
        )
        self.manager.userprofile.role = 'manager'
        self.manager.userprofile.save()
        
        self.employee = User.objects.create_user(
            username='employee',
            email='employee@example.com',
            password='testpass123'
        )
    
    def test_task_form_valid_data(self):
        """Test task form with valid data"""
        form_data = {
            'title': 'Test Task',
            'description': 'Test description that is long enough',
            'assigned_to': self.employee.pk,
            'priority': 'medium',
            'due_date': (timezone.now().date() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'estimated_hours': 8
        }
        form = TaskForm(data=form_data, created_by=self.manager)
        self.assertTrue(form.is_valid())
    
    def test_task_form_invalid_data(self):
        """Test task form with invalid data"""
        form_data = {
            'title': 'Test',  # Too short
            'description': 'Short',  # Too short
            'assigned_to': self.employee.pk,
            'priority': 'medium',
            'due_date': (timezone.now().date() - timedelta(days=1)).strftime('%Y-%m-%d'),  # Past date
            'estimated_hours': -1  # Negative hours
        }
        form = TaskForm(data=form_data, created_by=self.manager)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('description', form.errors)
        self.assertIn('due_date', form.errors)
        self.assertIn('estimated_hours', form.errors)


class UserRegistrationFormTest(TestCase):
    """Test user registration form (LO4.1)"""
    
    def test_registration_form_valid_data(self):
        """Test registration form with valid data"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'employee',
            'department': 'IT'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_registration_form_password_mismatch(self):
        """Test registration form with password mismatch"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'different123',
            'role': 'employee',
            'department': 'IT'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
    
    def test_registration_form_duplicate_username(self):
        """Test registration form with duplicate username"""
        # Create existing user
        User.objects.create_user(
            username='testuser',
            email='existing@example.com',
            password='testpass123'
        )
        
        form_data = {
            'username': 'testuser',  # Duplicate username
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'employee',
            'department': 'IT'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)


class PermissionTest(TestCase):
    """Test role-based permissions (LO4.1)"""
    
    def setUp(self):
        self.client = Client()
        
        # Create manager
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='testpass123'
        )
        self.manager.userprofile.role = 'manager'
        self.manager.userprofile.save()
        
        # Create employee
        self.employee = User.objects.create_user(
            username='employee',
            email='employee@example.com',
            password='testpass123'
        )
        
        # Create task
        self.task = Task.objects.create(
            title='Test Task',
            description='Test description',
            assigned_to=self.employee,
            created_by=self.manager,
            due_date=timezone.now().date() + timedelta(days=7)
        )
    
    def test_manager_can_create_task(self):
        """Test managers can create tasks"""
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('tasks:task_create'))
        self.assertEqual(response.status_code, 200)
    
    def test_employee_cannot_create_task(self):
        """Test employees cannot create tasks"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('tasks:task_create'))
        self.assertEqual(response.status_code, 403)
    
    def test_manager_can_access_dashboard(self):
        """Test managers can access manager dashboard"""
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('core:manager_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_employee_can_access_dashboard(self):
        """Test employees can access employee dashboard"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('core:employee_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_employee_cannot_access_manager_dashboard(self):
        """Test employees cannot access manager dashboard"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('core:manager_dashboard'))
        self.assertEqual(response.status_code, 403)


# JavaScript Test Documentation (LO4.2, LO4.3)
"""
JavaScript Testing Documentation

Manual Tests to Perform:

1. Login Form Tests:
   - Password visibility toggle functionality
   - Form validation (username/password length)
   - Loading state on form submission
   - Auto-focus on username field

2. Registration Form Tests:
   - Both password visibility toggles work
   - Real-time password match validation
   - Form validation for all required fields
   - Terms checkbox requirement

3. Task List Tests:
   - Search functionality with debounce
   - Filter dropdowns auto-submit
   - Quick status update buttons
   - Pagination navigation

4. Task Form Tests:
   - Priority preview updates
   - Due date minimum validation
   - Auto-resize textarea
   - Form validation before submission

5. Task Detail Tests:
   - Status update confirmations
   - Delete confirmation dialog
   - Comment form validation
   - Auto-resize comment textarea

Automated JavaScript Tests (using Jest/similar):

describe('Task Manager JavaScript', () => {
  test('Password toggle changes input type', () => {
    // Test password visibility toggle
  });
  
  test('Form validation prevents invalid submissions', () => {
    // Test client-side validation
  });
  
  test('AJAX status updates work correctly', () => {
    // Test async status updates
  });
  
  test('Search debounce works correctly', () => {
    // Test search delay functionality
  });
});

Responsive Design Tests:
- Test on mobile devices (320px width)
- Test on tablets (768px width)
- Test on desktop (1200px+ width)
- Verify Bootstrap grid system works
- Check navigation collapse on mobile

Accessibility Tests:
- Screen reader compatibility
- Keyboard navigation
- ARIA labels and descriptions
- Color contrast ratios
- Focus indicators

Usability Tests:
- Task creation workflow
- Task status updates
- Comment system
- Search and filtering
- Dashboard navigation
"""


# Performance Test Class
class PerformanceTest(TestCase):
    """Test application performance (LO4.1)"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test data
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='testpass123'
        )
        self.manager.userprofile.role = 'manager'
        self.manager.userprofile.save()
        
        # Create multiple employees
        self.employees = []
        for i in range(10):
            employee = User.objects.create_user(
                username=f'employee{i}',
                email=f'employee{i}@example.com',
                password='testpass123'
            )
            self.employees.append(employee)
        
        # Create multiple tasks
        for i in range(50):
            Task.objects.create(
                title=f'Test Task {i}',
                description=f'Description for task {i}',
                assigned_to=self.employees[i % len(self.employees)],
                created_by=self.manager,
                priority=['low', 'medium', 'high'][i % 3],
                due_date=timezone.now().date() + timedelta(days=i % 30)
            )
    
    def test_task_list_performance(self):
        """Test task list page loads efficiently with many tasks"""
        self.client.login(username='manager', password='testpass123')
        
        import time
        start_time = time.time()
        
        response = self.client.get(reverse('tasks:task_list'))
        
        end_time = time.time()
        load_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(load_time, 2.0)  # Should load in under 2 seconds
    
    def test_database_queries(self):
        """Test database query efficiency"""
        from django.test.utils import override_settings
        from django.db import connection
        
        self.client.login(username='manager', password='testpass123')
        
        with override_settings(DEBUG=True):
            connection.queries_log.clear()
            response = self.client.get(reverse('tasks:task_list'))
            
            # Should not exceed reasonable number of queries
            query_count = len(connection.queries)
            self.assertLess(query_count, 20)


if __name__ == '__main__':
    import unittest
    unittest.main()