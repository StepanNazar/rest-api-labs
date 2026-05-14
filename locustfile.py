from locust import HttpUser, task

class User(HttpUser):
    @task
    def get_books(self):
        self.client.get("/books/?limit=100")
