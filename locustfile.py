# locustfile.py
from locust import HttpUser, task, between


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)  # seconds between tasks

    def on_start(self):
        """
        If your site requires login, do a login POST here and store cookies.
        Example (adapt to your login URL and fields):

        response = self.client.post("/accounts/login/", {
            "username": "testuser",
            "password": "password123"
        })
        """

    @task(2)
    def view_dashboard(self):
        self.client.get("/")

    @task(3)
    def view_tasks(self):
        self.client.get("/tasks/")

    @task(1)
    def view_employee_dashboard(self):
        self.client.get("/dashboard/employee/")
