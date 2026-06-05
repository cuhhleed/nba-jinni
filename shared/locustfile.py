from locust import HttpUser, between, task

# Get the real URL by running in infra/environments/dev/:
#   terraform output -raw api_gateway_url
API_BASE = "https://yi03u7kjyd.execute-api.us-east-1.amazonaws.com"


class NBAJinniUser(HttpUser):
    host = API_BASE
    wait_time = between(1, 3)

    @task(3)
    def standings(self):
        self.client.get("/standings")

    @task(3)
    def standings_preview(self):
        self.client.get("/standings/preview")

    @task(2)
    def teams(self):
        self.client.get("/teams")

    @task(2)
    def players_search(self):
        self.client.get("/players/search?q=le")

    @task(1)
    def live_today(self):
        self.client.get("/games/live/today")
