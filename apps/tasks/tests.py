# apps/tasks/tests.py
"""
Test cases for tasks app
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Task, TaskComment
from .forms import TaskForm


class TaskModelTest(TestCase):
    """Test Task model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="testpass123",
        )
        self.manager.userprofile.role = "manager"
        self.manager.userprofile.save()

    def test_task_creation(self):
        """Test task creation"""
        task = Task.objects.create(
            title="Test Task",
            description="Test Description",
            assignee=self.user,
            created_by=self.manager,
            due_date=timezone.now() + timedelta(days=7),
        )
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.status, "pending")
        self.assertEqual(task.priority, "medium")

    def test_task_is_overdue(self):
        """Test is_overdue property"""
        # Future task
        future_task = Task.objects.create(
            title="Future Task",
            assignee=self.user,
            created_by=self.manager,
            due_date=timezone.now() + timedelta(days=7),
        )
        self.assertFalse(future_task.is_overdue)

        # Past task
        past_task = Task.objects.create(
            title="Past Task",
            assignee=self.user,
            created_by=self.manager,
            due_date=timezone.now() - timedelta(days=1),
        )
        self.assertTrue(past_task.is_overdue)

    def test_task_completion(self):
        """Test task completion"""
        task = Task.objects.create(
            title="Test Task",
            assignee=self.user,
            created_by=self.manager,
            due_date=timezone.now() + timedelta(days=7),
        )

        # Complete the task
        task.status = "completed"
        task.save()

        self.assertIsNotNone(task.completed_at)

    def test_get_priority_color(self):
        """Test get_priority_color method"""
        task = Task.objects.create(
            title="Test Task",
            assignee=self.user,
            created_by=self.manager,
            priority="high",
        )
        self.assertEqual(task.get_priority_color(), "text-danger")

        task.priority = "medium"
        self.assertEqual(task.get_priority_color(), "text-warning")

        task.priority = "low"
        self.assertEqual(task.get_priority_color(), "text-success")


class TaskFormTest(TestCase):
    """Test TaskForm"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="testpass123",
        )
        self.manager.userprofile.role = "manager"
        self.manager.userprofile.save()

    def test_valid_form(self):
        """Test form with valid data"""
        form_data = {
            "title": "Test Task",
            "description": "Test Description",
            "assignee": self.user.id,
            "priority": "high",
            "due_date": (
                timezone.now() + timedelta(days=7)
            ).strftime("%Y-%m-%d"),
        }
        form = TaskForm(data=form_data, user=self.manager)
        self.assertTrue(form.is_valid())

    def test_past_due_date(self):
        """Test form with past due date"""
        form_data = {
            "title": "Test Task",
            "description": "Test Description",
            "assignee": self.user.id,
            "priority": "high",
            "due_date": (
                timezone.now() - timedelta(days=1)
            ).strftime("%Y-%m-%d"),
        }
        form = TaskForm(data=form_data, user=self.manager)
        self.assertFalse(form.is_valid())
        self.assertIn("due_date", form.errors)


class TaskViewsTest(TestCase):
    """Test task views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.manager = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="testpass123",
        )
        self.manager.userprofile.role = "manager"
        self.manager.userprofile.save()

        self.task = Task.objects.create(
            title="Test Task",
            description="Test Description",
            assignee=self.user,
            created_by=self.manager,
            due_date=timezone.now() + timedelta(days=7),
        )

    def test_task_list_view(self):
        """Test task list view"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("tasks:task_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Task")

    def test_task_detail_view(self):
        """Test task detail view"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(
            reverse("tasks:task_detail", args=[self.task.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Task")

    def test_task_create_view_manager(self):
        """Test task create view for manager"""
        self.client.login(username="manager", password="testpass123")
        response = self.client.get(reverse("tasks:task_create"))
        self.assertEqual(response.status_code, 200)

    def test_task_create_view_employee(self):
        """Test task create view for employee (should be forbidden)"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("tasks:task_create"))
        self.assertEqual(response.status_code, 403)
