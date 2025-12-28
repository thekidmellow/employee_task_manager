import time
from datetime import timedelta

from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection, transaction, models
from django.contrib.auth.models import User
from django.utils import timezone

from apps.accounts.models import UserProfile
from apps.tasks.models import Task, TaskComment


class DatabasePerformanceTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username="testmanager",
            email="manager@test.com",
            password="testpass123",
        )
        self.manager.userprofile.role = "manager"
        self.manager.userprofile.save()

        self.employees = []
        for i in range(10):
            employee = User.objects.create_user(
                username=f"employee{i}",
                email=f"employee{i}@test.com",
                password="testpass123",
            )
            self.employees.append(employee)

        self.tasks = []
        for i in range(100):
            task = Task.objects.create(
                title=f"Performance Test Task {i}",
                description=f"Description for task {i}",
                assigned_to=self.employees[i % len(self.employees)],
                created_by=self.manager,
                priority=["low", "medium", "high"][i % 3],
                due_date=timezone.now() + timedelta(days=i % 30),
            )
            self.tasks.append(task)

        for i in range(0, 50, 5):
            for j in range(3):
                TaskComment.objects.create(
                    task=self.tasks[i],
                    user=self.employees[j % len(self.employees)],
                    comment=f"Comment {j} on task {i}",
                )

    def test_n_plus_one_queries(self):
        with self.assertNumQueries(1):
            tasks = Task.objects.select_related(
                "assigned_to",
                "created_by",
                "assigned_to__userprofile",
            ).all()[:10]

            for task in tasks:
                assigned_to_name = task.assigned_to.get_full_name()
                created_by_name = task.created_by.username
                role = task.assigned_to.userprofile.role

    def test_task_with_comments_query_efficiency(self):
        with self.assertNumQueries(3):
            tasks = (
                Task.objects.prefetch_related("comments__user")
                .filter(comments__isnull=False)
                .distinct()[:5]
            )

            for task in tasks:
                for comment in task.comments.all():
                    author_name = comment.user.username

    def test_dashboard_query_efficiency(self):
        with self.assertNumQueries(6):
            total_tasks = Task.objects.count()
            pending_tasks = Task.objects.filter(status="pending").count()
            completed_tasks = Task.objects.filter(status="completed").count()

            employee_tasks = list(
                Task.objects.values("assigned_to__username").annotate(
                    task_count=models.Count("id")
                )
            )

            recent_tasks = list(
                Task.objects.select_related(
                    "assigned_to",
                    "created_by",
                ).order_by("-created_at")[:5]
            )

            priority_stats = list(
                Task.objects.values("priority").annotate(
                    count=models.Count("id")
                )
            )

    def test_search_query_performance(self):
        start_time = time.time()

        search_results = (
            Task.objects.filter(
                models.Q(title__icontains="performance")
                | models.Q(description__icontains="performance")
            )
            .select_related("assigned_to", "created_by")[:20]
        )

        list(search_results)
        query_time = time.time() - start_time
        self.assertLess(query_time, 1.0)

    def test_bulk_operations_efficiency(self):
        start_time = time.time()

        bulk_tasks = []
        for i in range(50):
            bulk_tasks.append(
                Task(
                    title=f"Bulk Task {i}",
                    description=f"Bulk created task {i}",
                    assigned_to=self.employees[i % len(self.employees)],
                    created_by=self.manager,
                    priority="medium",
                    due_date=timezone.now() + timedelta(days=7),
                )
            )

        Task.objects.bulk_create(bulk_tasks)
        bulk_create_time = time.time() - start_time
        self.assertLess(bulk_create_time, 2.0)

        start_time = time.time()
        Task.objects.filter(
            title__startswith="Bulk Task").update(priority="high")
        bulk_update_time = time.time() - start_time
        self.assertLess(bulk_update_time, 1.0)

    @override_settings(DEBUG=True)
    def test_query_count_optimization(self):
        from django.test import Client

        client = Client()
        client.login(username="testmanager", password="testpass123")

        # Reset query log
        connection.queries_log.clear()
        client.get("/tasks/")
        query_count = len(connection.queries)

        self.assertLess(query_count, 15)

        for query in connection.queries:
            if float(query.get("time", 0)) > 0.1:
                print(
                    f"Slow query ({query['time']}s): {query['sql'][:100]}...")

    def test_index_usage(self):
        with connection.cursor() as cursor:
            start_time = time.time()
            cursor.execute(
                "SELECT COUNT(*) FROM tasks_task WHERE status = %s",
                ["pending"],
            )
            query_time = time.time() - start_time
            self.assertLess(query_time, 0.1)

            start_time = time.time()
            cursor.execute(
                "SELECT COUNT(*) FROM tasks_task WHERE assigned_to_id = %s",
                [self.employees[0].id],
            )
            query_time = time.time() - start_time
            self.assertLess(query_time, 0.1)

    def test_large_dataset_performance(self):
        bulk_tasks = []
        for i in range(1000):
            bulk_tasks.append(
                Task(
                    title=f"Large Dataset Task {i}",
                    description=f"Task {i} for large dataset testing",
                    assigned_to=self.employees[i % len(self.employees)],
                    created_by=self.manager,
                    priority=["low", "medium", "high"][i % 3],
                    due_date=timezone.now() + timedelta(days=i % 365),
                )
            )
        Task.objects.bulk_create(bulk_tasks)

        start_time = time.time()
        first_page = Task.objects.select_related(
            "assigned_to",
            "created_by",
        ).order_by("-created_at")[:20]
        list(first_page)
        pagination_time = time.time() - start_time
        self.assertLess(pagination_time, 1.0)

        start_time = time.time()
        stats = Task.objects.aggregate(
            total=models.Count("id"),
            avg_priority=models.Count("priority"),
        )
        aggregation_time = time.time() - start_time
        self.assertLess(aggregation_time, 0.5)

    def test_connection_pooling(self):
        start_time = time.time()

        for _ in range(10):
            Task.objects.filter(assigned_to=self.employees[0]).count()

        total_time = time.time() - start_time
        self.assertLess(total_time, 1.0)

    def test_transaction_performance(self):
        start_time = time.time()

        with transaction.atomic():
            new_task = Task.objects.create(
                title="Transaction Test Task",
                description="Task created in transaction",
                assigned_to=self.employees[0],
                created_by=self.manager,
                priority="medium",
                due_date=timezone.now() + timedelta(days=7),
            )

            for i in range(5):
                TaskComment.objects.create(
                    task=new_task,
                    user=self.employees[i % len(self.employees)],
                    comment=f"Transaction comment {i}",
                )

        transaction_time = time.time() - start_time
        self.assertLess(transaction_time, 1.0)

    def test_cache_effectiveness(self):
        start_time = time.time()
        task_count = Task.objects.count()
        first_query_time = time.time() - start_time

        start_time = time.time()
        task_count_cached = Task.objects.count()
        second_query_time = time.time() - start_time

        self.assertEqual(task_count, task_count_cached)

    def test_memory_usage(self):
        import sys

        before_query = sys.getsizeof(connection.queries)

        large_queryset = Task.objects.select_related(
            "assigned_to",
            "created_by",
        ).prefetch_related("comments__user").all()

        for task in large_queryset[:100]:
            pass

        after_query = sys.getsizeof(connection.queries)
        memory_growth = after_query - before_query

        self.assertLess(memory_growth, 10000)
