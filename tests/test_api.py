import json
from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import UserProfile
from apps.tasks.models import Task, TaskComment


class TaskAPITests(TestCase):

    def setUp(self):
        self.client = Client()

        self.manager = User.objects.create_user(
            username='testmanager',
            password='testpass123'
        )
        profile = UserProfile.objects.get(user=self.manager)
        profile.role = 'manager'
        profile.save()
        self.manager.is_staff = True
        self.manager.is_superuser = True
        self.manager.save()

        managers_group, _ = Group.objects.get_or_create(name='Managers')
        self.manager.groups.add(managers_group)

        self.employee = User.objects.create_user(
            username='testemployee',
            password='testpass123'
        )
        profile = UserProfile.objects.get(user=self.employee)
        profile.role = 'employee'
        profile.save()

        employees_group, _ = Group.objects.get_or_create(name='Employees')
        self.employee.groups.add(employees_group)

        self.task = Task.objects.create(
            title='API Test Task',
            description='Test Description',
            assigned_to=self.employee,
            created_by=self.manager,
            priority='medium',
            due_date=timezone.now() + timedelta(days=7)
        )

    def test_user_list_api(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse('accounts:user_list_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('users', data)
        self.assertGreaterEqual(len(data['users']), 2)

    def test_task_comment_api(self):
        self.client.force_login(self.employee)

        response = self.client.post(
            reverse('tasks:task_comment_api'),
            data={
                'task_id': self.task.id,
                'comment': 'Test comment from API'
            }
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))

        comment = TaskComment.objects.filter(task=self.task).first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.comment, 'Test comment from API')
        self.assertEqual(comment.user, self.employee)
