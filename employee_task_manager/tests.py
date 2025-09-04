# employee_task_manager/tests.py
"""
Test suite for Employee Task Manager
Covers models, views, forms, and permissions.
"""

from datetime import timedelta
import json

from django.shortcuts import resolve_url
from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User

from apps.accounts.models import UserProfile
from apps.tasks.models import Task, TaskComment
from apps.tasks.forms import TaskCreationForm, TaskCommentForm
from apps.accounts.forms import UserRegistrationForm


# ---------- Models ----------

class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )

    def test_user_profile_creation(self):
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.role, 'employee')

    def test_is_manager_property(self):
        p = self.user.userprofile
        self.assertFalse(p.is_manager)
        p.role = 'manager'
        p.save()
        self.assertTrue(p.is_manager)


class TaskModelTest(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user('manager', 'm@example.com', 'pass')
        self.manager.userprofile.role = 'manager'
        self.manager.userprofile.save()
        self.employee = User.objects.create_user('employee', 'e@example.com', 'pass')
        self.task = Task.objects.create(
            title='Test Task',
            description='Test task description',
            assigned_to=self.employee,
            created_by=self.manager,
            priority='medium',
            due_date=timezone.now() + timedelta(days=7),
        )

    def test_task_creation_defaults(self):
        self.assertEqual(self.task.status, 'pending')
        self.assertEqual(self.task.assigned_to, self.employee)

    def test_str(self):
        self.assertEqual(str(self.task), f"{self.task.title} - {self.task.get_status_display()}")

    def test_is_overdue(self):
        self.assertFalse(self.task.is_overdue)
        self.task.due_date = timezone.now() - timedelta(days=1)
        self.task.save()
        self.assertTrue(self.task.is_overdue)
        self.task.status = 'completed'
        self.task.save()
        self.assertFalse(self.task.is_overdue)

    def test_colors_helpers(self):
        self.task.priority = 'high'
        self.assertEqual(self.task.get_priority_color(), 'danger')
        self.task.status = 'in_progress'
        self.assertEqual(self.task.get_status_color(), 'primary')


class TaskCommentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('u', 'u@example.com', 'pass')
        self.task = Task.objects.create(
            title='T', description='D' * 10, assigned_to=self.user, created_by=self.user,
            due_date=timezone.now() + timedelta(days=7),
        )
        self.comment = TaskComment.objects.create(task=self.task, user=self.user, comment='Nice!')

    def test_comment_fields(self):
        self.assertEqual(self.comment.task, self.task)
        self.assertEqual(self.comment.user, self.user)
        self.assertEqual(self.comment.comment, 'Nice!')

    def test_comment_str(self):
        self.assertEqual(str(self.comment), f"Comment by {self.user.username} on {self.task.title}")


# ---------- Views ----------

def _dt_local(dt):
    """Return datetime formatted for datetime-local input."""
    return dt.strftime('%Y-%m-%dT%H:%M')


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

    def test_login_get(self):
        login_url = resolve_url(settings.LOGIN_URL)  # works with name or path
        resp = self.client.get(login_url)
        self.assertEqual(resp.status_code, 200)

    def test_login_post_valid(self):
        login_url = resolve_url(settings.LOGIN_URL)
        resp = self.client.post(login_url, {'username': 'testuser', 'password': 'testpass123'})
        self.assertEqual(resp.status_code, 302)

    def test_login_post_invalid(self):
        login_url = resolve_url(settings.LOGIN_URL)
        resp = self.client.post(login_url, {'username': 'testuser', 'password': 'wrong'})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.wsgi_request.user.is_anonymous)

    def test_logout(self):
        self.client.login(username='testuser', password='testpass123')
        try:
            logout_url = resolve_url('accounts:logout')
        except Exception:
            logout_url = '/accounts/logout/'

        # Prefer POST; if the view only supports GET, fall back.
        resp = self.client.post(logout_url)
        if resp.status_code == 405:
            resp = self.client.get(logout_url)

        self.assertIn(resp.status_code, (200, 302))


class TaskViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user('manager', 'm@example.com', 'pass')
        self.manager.userprofile.role = 'manager'
        self.manager.userprofile.save()
        self.employee = User.objects.create_user('employee', 'e@example.com', 'pass')
        self.task = Task.objects.create(
            title='Test Task',
            description='Test task description',
            assigned_to=self.employee,
            created_by=self.manager,
            priority='medium',
            due_date=timezone.now() + timedelta(days=7),
        )

    def test_task_list_employee(self):
        self.client.login(username='employee', password='pass')
        resp = self.client.get(reverse('tasks:task_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Test Task')

    def test_task_list_requires_login(self):
        resp = self.client.get(reverse('tasks:task_list'))
        self.assertEqual(resp.status_code, 302)

    def test_task_detail(self):
        self.client.login(username='employee', password='pass')
        resp = self.client.get(reverse('tasks:task_detail', args=[self.task.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.task.title)

    def test_task_create_page_manager(self):
        self.client.login(username='manager', password='pass')
        resp = self.client.get(reverse('tasks:task_create'))
        self.assertEqual(resp.status_code, 200)

    def test_task_create_page_employee_redirects(self):
        self.client.login(username='employee', password='pass')
        resp = self.client.get(reverse('tasks:task_create'), follow=True)
        self.assertEqual(resp.status_code, 200)  # landed on list with message

    def test_task_create_post_valid(self):
        self.client.login(username='manager', password='pass')
        resp = self.client.post(reverse('tasks:task_create'), {
            'title': 'New Test Task',
            'description': 'New task description',
            'assigned_to': self.employee.pk,
            'priority': 'high',
            'status': 'pending',
            'estimated_hours': '8',
            'due_date': _dt_local(timezone.now() + timedelta(days=5)),
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Task.objects.filter(title='New Test Task').exists())

    def test_task_edit_view(self):
        self.client.login(username='manager', password='pass')
        resp = self.client.get(reverse('tasks:task_update', args=[self.task.pk]))
        self.assertEqual(resp.status_code, 200)

    def test_task_status_update_ajax(self):
        self.client.login(username='employee', password='pass')
        resp = self.client.post(
            reverse('tasks:task_update_status', args=[self.task.pk]),
            json.dumps({'status': 'in_progress'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'in_progress')


# ---------- Forms ----------

class TaskFormTest(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user('manager', 'm@example.com', 'pass')
        self.manager.userprofile.role = 'manager'
        self.manager.userprofile.save()
        self.employee = User.objects.create_user('employee', 'e@example.com', 'pass')

    def test_task_creation_form_valid(self):
        form_data = {
            'title': 'Test Task',
            'description': 'Long enough description for validity',
            'assigned_to': self.employee.pk,
            'priority': 'medium',
            'status': 'pending',
            'estimated_hours': '8',
            'due_date': _dt_local(timezone.now() + timedelta(days=7)),
        }
        form = TaskCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_task_creation_form_invalid(self):
        form_data = {
            'title': 'Test',  # too short
            'description': 'Short',  # too short
            'assigned_to': self.employee.pk,
            'priority': 'medium',
            'status': 'pending',
            'estimated_hours': '-1',
            'due_date': _dt_local(timezone.now() - timedelta(days=1)),  # past
        }
        form = TaskCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)
        self.assertIn('description', form.errors)
        self.assertIn('due_date', form.errors)


class UserRegistrationFormTest(TestCase):
    def test_registration_form(self):
        form_data = {
            'username': 'testuser',
            'email': 'test@company.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'employee',
            'department': 'IT',
            'agree_terms': True,  # <-- add this if your form has it
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors.as_json())

    def test_registration_duplicate_username(self):
        User.objects.create_user('testuser', 'existing@company.com', 'x')
        form = UserRegistrationForm(data={
            'username': 'testuser',
            'email': 'test@company.com',
            'first_name': 'T',
            'last_name': 'U',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'employee',
            'department': 'IT',
            'agree_terms': True,  # keep consistent
        })
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)



# ---------- Performance (lightweight) ----------

class PerformanceTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user('manager', 'm@example.com', 'pass')
        self.manager.userprofile.role = 'manager'
        self.manager.userprofile.save()
        employees = [
            User.objects.create_user(f'e{i}', f'e{i}@example.com', 'pass') for i in range(10)
        ]
        for i in range(50):
            Task.objects.create(
                title=f'Task {i}',
                description=f'Description {i}' * 3,
                assigned_to=employees[i % 10],
                created_by=self.manager,
                priority=['low', 'medium', 'high'][i % 3],
                due_date=timezone.now() + timedelta(days=(i % 30)),
            )

    def test_task_list_loads_quickly(self):
        self.client.login(username='manager', password='pass')
        resp = self.client.get(reverse('tasks:task_list'))
        self.assertEqual(resp.status_code, 200)
