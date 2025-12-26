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
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_profile_creation(self):
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.role, 'employee')
    
    def test_is_manager_property(self):
        profile = self.user.userprofile
        self.assertFalse(profile.is_manager)
        
        profile.role = 'manager'
        profile.save()
        self.assertTrue(profile.is_manager)
    
    def test_get_role_display(self):
        profile = self.user.userprofile
        self.assertEqual(profile.get_role_display(), 'Employee')
        
        profile.role = 'manager'
        self.assertEqual(profile.get_role_display(), 'Manager')


class TaskModelTest(TestCase):
    
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
        self.assertEqual(self.task.title, 'Test Task')
        self.assertEqual(self.task.status, 'pending')
        self.assertEqual(self.task.assigned_to, self.employee)
        self.assertEqual(self.task.created_by, self.manager)
    
    def test_task_str_method(self):
        expected_str = f"{self.task.title} - {self.employee.username}"
        self.assertEqual(str(self.task), expected_str)
    
    def test_is_overdue_property(self):
        self.assertFalse(self.task.is_overdue)
        
        self.task.due_date = timezone.now().date() - timedelta(days=1)
        self.task.save()
        self.assertTrue(self.task.is_overdue)
        
        self.task.status = 'completed'
        self.task.save()
        self.assertFalse(self.task.is_overdue)
    
    def test_get_progress_percentage(self):
        self.assertEqual(self.task.get_progress_percentage(), 0)
        
        self.task.status = 'in_progress'
        self.assertEqual(self.task.get_progress_percentage(), 50)
        
        self.task.status = 'completed'
        self.assertEqual(self.task.get_progress_percentage(), 100)
    
    def test_get_priority_color(self):
        self.task.priority = 'high'
        self.assertEqual(self.task.get_priority_color(), 'danger')
        
        self.task.priority = 'medium'
        self.assertEqual(self.task.get_priority_color(), 'warning')
        
        self.task.priority = 'low'
        self.assertEqual(self.task.get_priority_color(), 'success')


class TaskCommentModelTest(TestCase):
    
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
        self.assertEqual(self.comment.task, self.task)
        self.assertEqual(self.comment.author, self.user)
        self.assertEqual(self.comment.content, 'Test comment')
    
    def test_comment_str_method(self):
        expected_str = f"Comment by {self.user.username} on {self.task.title}"
        self.assertEqual(str(self.comment), expected_str)


class AuthenticationViewTest(TestCase):
    
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
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Login to Your Account')
    
    def test_login_view_post_valid(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
    
    def test_login_view_post_invalid(self):
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct username and password')
    
    def test_logout_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
    
    def test_registration_view_get(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Your Account')
    
    def test_registration_view_post_valid(self):
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
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())


class TaskViewTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        
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
    
    def test_task_list_view_authenticated(self):
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('tasks:task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Task')
    
    def test_task_list_view_unauthenticated(self):
        response = self.client.get(reverse('tasks:task_list'))
        self.assertEqual(response.status_code, 302)
    
    def test_task_detail_view(self):
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('tasks:task_detail', args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.task.title)
        self.assertContains(response, self.task.description)
    
    def test_task_create_view_manager(self):
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('tasks:task_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create New Task')
    
    def test_task_create_view_employee_forbidden(self):
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('tasks:task_create'))
        self.assertEqual(response.status_code, 403)
    
    def test_task_create_post_valid(self):
        self.client.login(username='manager', password='testpass123')
        response = self.client.post(reverse('tasks:task_create'), {
            'title': 'New Test Task',
            'description': 'New task description',
            'assigned_to': self.employee.pk,
            'priority': 'high',
            'due_date': (timezone.now().date() + timedelta(days=5)).strftime('%Y-%m-%d'),
            'estimated_hours': 8
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(title='New Test Task').exists())
    
    def test_task_edit_view_authorized(self):
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('tasks:task_edit', args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Task')
    
    def test_task_status_update_ajax(self):
        self.client.login(username='employee', password='testpass123')
        response = self.client.post(
            reverse('tasks:task_update_status', args=[self.task.pk]),
            json.dumps({'status': 'in_progress'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'in_progress')


class TaskFormTest(TestCase):
    
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
        form_data = {
            'title': 'Test',
            'description': 'Short',
            'assigned_to': self.employee.pk,
            'priority': 'medium',
            'due_date': (timezone.now().date() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'estimated_hours': -1
        }
        form = TaskForm(data=form_data, created_by=self.manager)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('description', form.errors)
        self.assertIn('due_date', form.errors)
        self.assertIn('estimated_hours', form.errors)


class UserRegistrationFormTest(TestCase):
    
    def test_registration_form_valid_data(self):
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
        User.objects.create_user(
            username='testuser',
            email='existing@example.com',
            password='testpass123'
        )
        
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
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)


class PermissionTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        
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
            description='Test description',
            assigned_to=self.employee,
            created_by=self.manager,
            due_date=timezone.now().date() + timedelta(days=7)
        )
    
    def test_manager_can_create_task(self):
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('tasks:task_create'))
        self.assertEqual(response.status_code, 200)
    
    def test_employee_cannot_create_task(self):
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('tasks:task_create'))
        self.assertEqual(response.status_code, 403)
    
    def test_manager_can_access_dashboard(self):
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('core:manager_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_employee_can_access_dashboard(self):
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('core:employee_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_employee_cannot_access_manager_dashboard(self):
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('core:manager_dashboard'))
        self.assertEqual(response.status_code, 403)


class PerformanceTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='testpass123'
        )
        self.manager.userprofile.role = 'manager'
        self.manager.userprofile.save()
        
        self.employees = []
        for i in range(10):
            employee = User.objects.create_user(
                username=f'employee{i}',
                email=f'employee{i}@example.com',
                password='testpass123'
            )
            self.employees.append(employee)
        
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
        self.client.login(username='manager', password='testpass123')
        
        import time
        start_time = time.time()
        
        response = self.client.get(reverse('tasks:task_list'))
        
        end_time = time.time()
        load_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(load_time, 2.0)
    
    def test_database_queries(self):
        from django.test.utils import override_settings
        from django.db import connection
        
        self.client.login(username='manager', password='testpass123')
        
        with override_settings(DEBUG=True):
            connection.queries_log.clear()
            response = self.client.get(reverse('tasks:task_list'))
            
            query_count = len(connection.queries)
            self.assertLess(query_count, 20)


if __name__ == '__main__':
    import unittest
    unittest.main()
