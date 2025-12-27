import random
from locust import HttpUser, task, between
from locust.exception import ResponseError


class TaskManagerUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.login()

    def login(self):
        response = self.client.get("/login/")

        if response.status_code == 200:
            login_response = self.client.post("/login/", {
                "username": "testemployee",
                "password": "testpass123",
            }, catch_response=True)

            if login_response.status_code == 302:
                login_response.success()
            else:
                login_response.failure(
                    f"Login failed: {login_response.status_code}")

    @task(3)
    def view_task_list(self):
        with self.client.get("/tasks/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Task list failed: {response.status_code}")

    @task(2)
    def view_dashboard(self):
        with self.client.get("/dashboard/employee/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard failed: {response.status_code}")

    @task(1)
    def view_task_detail(self):
        task_id = random.randint(1, 10)

        with self.client.get(f"/tasks/{task_id}/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()
            else:
                response.failure(f"Task detail failed: {response.status_code}")

    @task(1)
    def search_tasks(self):
        search_terms = ["setup", "test", "database", "api", "fix"]
        search_term = random.choice(search_terms)

        with self.client.get(f"/tasks/?search={search_term}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Search failed: {response.status_code}")

    @task(1)
    def filter_tasks(self):
        filters = [
            {"status": "pending"},
            {"status": "in_progress"},
            {"status": "completed"},
            {"priority": "high"},
            {"priority": "medium"},
            {"priority": "low"}
        ]

        filter_params = random.choice(filters)

        with self.client.get("/tasks/", params=filter_params, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Filter failed: {response.status_code}")

    @task(1)
    def view_profile(self):
        with self.client.get("/accounts/profile/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Profile failed: {response.status_code}")

    @task(1)
    def api_task_stats(self):
        headers = {"X-Requested-With": "XMLHttpRequest"}

        with self.client.get("/tasks/api/stats/", headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    response.json()
                    response.success()
                except ValueError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"API stats failed: {response.status_code}")


class ManagerUser(HttpUser):
    wait_time = between(2, 5)
    weight = 1

    def on_start(self):
        self.login()

    def login(self):
        response = self.client.get("/login/")

        if response.status_code == 200:
            login_response = self.client.post("/login/", {
                "username": "testmanager",
                "password": "testpass123",
            }, catch_response=True)

            if login_response.status_code == 302:
                login_response.success()
            else:
                login_response.failure(
                    f"Manager login failed: {login_response.status_code}")

    @task(3)
    def view_manager_dashboard(self):
        with self.client.get("/dashboard/manager/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Manager dashboard failed: {response.status_code}")

    @task(2)
    def view_all_tasks(self):
        with self.client.get("/tasks/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"All tasks view failed: {response.status_code}")

    @task(1)
    def create_task_form(self):
        with self.client.get("/tasks/create/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Create task form failed: {response.status_code}")

    @task(1)
    def api_user_list(self):
        headers = {"X-Requested-With": "XMLHttpRequest"}

        with self.client.get("/accounts/api/users/", headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    users = response.json()
                    if isinstance(users, list):
                        response.success()
                    else:
                        response.failure("Invalid user list format")
                except ValueError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(
                    f"User list API failed: {response.status_code}")


class AnonymousUser(HttpUser):
    wait_time = between(3, 8)
    weight = 2

    @task(5)
    def view_homepage(self):
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Homepage failed: {response.status_code}")

    @task(2)
    def view_login_page(self):
        with self.client.get("/login/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Login page failed: {response.status_code}")

    @task(1)
    def view_register_page(self):
        with self.client.get("/accounts/register/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Register page failed: {response.status_code}")

    @task(1)
    def test_protected_page(self):
        with self.client.get("/tasks/", catch_response=True) as response:
            if response.status_code == 302:
                response.success()
            else:
                response.failure(
                    f"Protected page access failed: {response.status_code}")


class StressTestUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self):
        self.login()

    def login(self):
        response = self.client.get("/login/")
        self.client.post("/login/", {
            "username": "testemployee",
            "password": "testpass123",
        })

    @task
    def rapid_task_list_access(self):
        self.client.get("/tasks/")

    @task
    def rapid_dashboard_access(self):
        self.client.get("/dashboard/employee/")


class SpikeTestUser(HttpUser):
    wait_time = between(0, 1)

    def on_start(self):
        self.login()

    def login(self):
        response = self.client.get("/login/")
        self.client.post("/login/", {
            "username": "testemployee",
            "password": "testpass123",
        })

    @task(10)
    def concurrent_task_access(self):
        self.client.get("/tasks/")
        self.client.get("/dashboard/employee/")
        self.client.get("/tasks/api/stats/",
                        headers={"X-Requested-With": "XMLHttpRequest"})
