"""
Locust Load Testing Configuration
For continuous and distributed load testing

Run with:
    locust -f tests/locustfile.py --host=http://localhost:8000

Features:
- Multi-tenant user simulation
- Batch processing scenarios
- API endpoint testing
- WebSocket connections
- Performance monitoring
"""

from locust import HttpUser, task, between, events
import json
import random
import time


class TenantUser(HttpUser):
    """Simulates a tenant user accessing the system"""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Called when a user starts"""
        self.tenant_id = f"tenant_{random.randint(1, 100)}"
        self.queries = [
            "Analyze this text for sentiment",
            "Generate a summary of the following",
            "Translate this to Spanish",
            "Extract key information",
            "Classify this document",
        ]

    @task(5)
    def execute_query(self):
        """Execute a standard query (highest weight)"""
        query = random.choice(self.queries)
        headers = {"Content-Type": "application/json", "X-Tenant-ID": self.tenant_id}

        payload = {"query": query, "enable_optimization": False}

        with self.client.post(
            "/v2/execute", json=payload, headers=headers, catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def execute_with_optimization(self):
        """Execute query with optimization enabled"""
        query = random.choice(self.queries)
        headers = {"Content-Type": "application/json", "X-Tenant-ID": self.tenant_id}

        payload = {"query": query, "enable_optimization": True}

        with self.client.post(
            "/v2/execute", json=payload, headers=headers, catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(3)
    def check_health(self):
        """Check system health"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")

    @task(1)
    def submit_batch(self):
        """Submit a batch job"""
        headers = {"Content-Type": "application/json", "X-Tenant-ID": self.tenant_id}

        batch_items = [
            {"query": random.choice(self.queries), "item_id": i} for i in range(10)
        ]

        payload = {
            "items": batch_items,
            "priority": random.choice(["low", "normal", "high"]),
        }

        with self.client.post(
            "/v2/batch", json=payload, headers=headers, catch_response=True
        ) as response:
            if response.status_code in [200, 201, 202]:
                response.success()
            else:
                response.failure(f"Batch submission failed: {response.status_code}")


class BatchProcessingUser(HttpUser):
    """Simulates batch processing workloads"""

    wait_time = between(2, 5)

    def on_start(self):
        """Called when a user starts"""
        self.tenant_id = f"batch_tenant_{random.randint(1, 20)}"

    @task(10)
    def submit_large_batch(self):
        """Submit a large batch job"""
        headers = {"Content-Type": "application/json", "X-Tenant-ID": self.tenant_id}

        batch_items = [
            {"query": f"Process item {i}", "item_id": i} for i in range(50)
        ]

        payload = {"items": batch_items, "priority": "normal"}

        with self.client.post(
            "/v2/batch", json=payload, headers=headers, catch_response=True
        ) as response:
            if response.status_code in [200, 201, 202]:
                batch_id = response.json().get("batch_id")
                if batch_id:
                    self.batch_id = batch_id
                response.success()
            else:
                response.failure(f"Batch submission failed: {response.status_code}")

    @task(5)
    def check_batch_status(self):
        """Check status of submitted batch"""
        if hasattr(self, "batch_id"):
            headers = {"X-Tenant-ID": self.tenant_id}

            with self.client.get(
                f"/v2/batch/{self.batch_id}", headers=headers, catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Status check failed: {response.status_code}")

    @task(2)
    def list_batches(self):
        """List all batches for tenant"""
        headers = {"X-Tenant-ID": self.tenant_id}

        with self.client.get(
            "/v2/batch", headers=headers, catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"List batches failed: {response.status_code}")


class StressTestUser(HttpUser):
    """High-intensity stress testing user"""

    wait_time = between(0.1, 0.5)  # Very short wait time

    def on_start(self):
        """Called when a user starts"""
        self.tenant_id = f"stress_tenant_{random.randint(1, 10)}"

    @task(20)
    def rapid_fire_requests(self):
        """Fire requests rapidly"""
        headers = {"Content-Type": "application/json", "X-Tenant-ID": self.tenant_id}

        payload = {"query": "Quick query", "enable_optimization": False}

        with self.client.post(
            "/v2/execute", json=payload, headers=headers, catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                # Rate limited - expected under stress
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(5)
    def concurrent_requests(self):
        """Simulate concurrent requests from same user"""
        headers = {"Content-Type": "application/json", "X-Tenant-ID": self.tenant_id}

        # Fire multiple requests quickly
        for i in range(5):
            payload = {"query": f"Concurrent query {i}", "enable_optimization": False}
            self.client.post("/v2/execute", json=payload, headers=headers)


# Custom event handlers for monitoring
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("🚀 Load test starting...")
    print(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    print("🏁 Load test complete!")
    stats = environment.stats

    print("\n" + "=" * 60)
    print("LOAD TEST SUMMARY")
    print("=" * 60)

    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Failed requests: {stats.total.num_failures}")
    print(
        f"Success rate: {((stats.total.num_requests - stats.total.num_failures) / max(stats.total.num_requests, 1)) * 100:.2f}%"
    )

    print(f"\nAverage response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Median response time: {stats.total.median_response_time:.2f}ms")
    print(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")

    print(f"\nRequests per second: {stats.total.total_rps:.2f}")
    print(f"Max RPS: {stats.total.max_requests_per_second:.2f}")

    print("\n" + "=" * 60)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Called on every request"""
    if exception:
        print(f"❌ Request failed: {name} - {exception}")


# Example usage:
# For normal load testing:
#   locust -f tests/locustfile.py --host=http://localhost:8000
#
# For stress testing:
#   locust -f tests/locustfile.py --host=http://localhost:8000 -u 100 -r 10
#
# For distributed testing:
#   Master: locust -f tests/locustfile.py --master --host=http://localhost:8000
#   Worker: locust -f tests/locustfile.py --worker --master-host=<master-ip>
#
# Headless mode:
#   locust -f tests/locustfile.py --host=http://localhost:8000 --headless -u 50 -r 5 -t 300
