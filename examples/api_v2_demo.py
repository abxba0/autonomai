"""
Example client demonstrating advanced API features

This example shows how to use:
- REST API endpoints
- GraphQL queries and mutations
- WebSocket real-time updates
- Webhook registration and verification
"""

import asyncio
import json
import requests
import websockets
from typing import Optional


class AutonomAIClient:
    """Client for interacting with AutonomAI API v2"""

    def __init__(self, base_url: str = "http://localhost:8000/v2"):
        self.base_url = base_url
        self.graphql_url = f"{base_url}/graphql"
        self.ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")

    # ============ REST API Methods ============

    def execute_query(self, query: str, context: Optional[list] = None) -> dict:
        """Execute a query using REST API"""
        response = requests.post(
            f"{self.base_url}/execute",
            json={"query": query, "conversation_context": context},
        )
        response.raise_for_status()
        return response.json()

    def provide_feedback(
        self, feedback: str, severity: str = "moderate", attach_output: bool = True
    ) -> dict:
        """Provide feedback using REST API"""
        response = requests.post(
            f"{self.base_url}/feedback",
            json={
                "feedback": feedback,
                "severity": severity,
                "attach_last_output": attach_output,
            },
        )
        response.raise_for_status()
        return response.json()

    def get_status(self) -> dict:
        """Get system status using REST API"""
        response = requests.get(f"{self.base_url}/status")
        response.raise_for_status()
        return response.json()

    def get_versions(self) -> list:
        """Get version history using REST API"""
        response = requests.get(f"{self.base_url}/versions")
        response.raise_for_status()
        return response.json()

    # ============ GraphQL Methods ============

    def graphql_query(self, query: str, variables: Optional[dict] = None) -> dict:
        """Execute a GraphQL query"""
        response = requests.post(
            self.graphql_url, json={"query": query, "variables": variables}
        )
        response.raise_for_status()
        return response.json()

    def graphql_get_status(self) -> dict:
        """Get system status using GraphQL"""
        query = """
        query {
            status {
                totalFailures
                totalOptimizations
                currentVersion
                lastOptimization
                systemHealth
            }
        }
        """
        result = self.graphql_query(query)
        return result["data"]["status"]

    def graphql_get_versions(self) -> list:
        """Get version history using GraphQL"""
        query = """
        query {
            versions {
                versionId
                timestamp
                triggerType
                diffSummary
                rulesAdded
                rulesModified
                rulesDeprecated
            }
        }
        """
        result = self.graphql_query(query)
        return result["data"]["versions"]

    def graphql_execute(self, user_query: str) -> dict:
        """Execute a query using GraphQL mutation"""
        mutation = """
        mutation($query: String!) {
            execute(input: {query: $query}) {
                output
                validationPassed
                optimizationAttempted
                validationResults {
                    validatorName
                    passed
                    errorMessage
                }
            }
        }
        """
        result = self.graphql_query(mutation, {"query": user_query})
        return result["data"]["execute"]

    # ============ Webhook Methods ============

    def register_webhook(
        self, url: str, events: list, secret: Optional[str] = None
    ) -> dict:
        """Register a webhook"""
        response = requests.post(
            f"{self.base_url}/webhooks",
            json={"url": url, "events": events, "secret": secret},
        )
        response.raise_for_status()
        return response.json()

    def list_webhooks(self) -> list:
        """List all registered webhooks"""
        response = requests.get(f"{self.base_url}/webhooks")
        response.raise_for_status()
        return response.json()

    def unregister_webhook(self, webhook_id: str) -> dict:
        """Unregister a webhook"""
        response = requests.delete(f"{self.base_url}/webhooks/{webhook_id}")
        response.raise_for_status()
        return response.json()

    def activate_webhook(self, webhook_id: str) -> dict:
        """Activate a webhook"""
        response = requests.post(f"{self.base_url}/webhooks/{webhook_id}/activate")
        response.raise_for_status()
        return response.json()

    def deactivate_webhook(self, webhook_id: str) -> dict:
        """Deactivate a webhook"""
        response = requests.post(f"{self.base_url}/webhooks/{webhook_id}/deactivate")
        response.raise_for_status()
        return response.json()

    # ============ WebSocket Methods ============

    async def listen_to_jobs(self, callback):
        """Listen to job updates via WebSocket"""
        uri = f"{self.ws_url}/ws/jobs"
        async with websockets.connect(uri) as websocket:
            # Subscribe to jobs channel
            await websocket.send(
                json.dumps({"type": "subscribe", "channel": "jobs"})
            )

            # Listen for messages
            async for message in websocket:
                data = json.loads(message)
                await callback(data)

    async def listen_to_workflows(self, callback):
        """Listen to workflow updates via WebSocket"""
        uri = f"{self.ws_url}/ws/workflows"
        async with websockets.connect(uri) as websocket:
            # Subscribe to workflows channel
            await websocket.send(
                json.dumps({"type": "subscribe", "channel": "workflows"})
            )

            # Listen for messages
            async for message in websocket:
                data = json.loads(message)
                await callback(data)

    async def listen_to_all(self, callback):
        """Listen to all updates via general WebSocket"""
        uri = f"{self.ws_url}/ws"
        async with websockets.connect(uri) as websocket:
            # Subscribe to all channels
            for channel in ["jobs", "workflows", "optimizations", "regressions"]:
                await websocket.send(
                    json.dumps({"type": "subscribe", "channel": channel})
                )

            # Listen for messages
            async for message in websocket:
                data = json.loads(message)
                await callback(data)


# ============ Example Usage ============


def example_rest_api():
    """Example: Using REST API"""
    print("\n=== REST API Example ===\n")

    client = AutonomAIClient()

    # Execute a query
    print("1. Executing query...")
    result = client.execute_query("Explain machine learning in simple terms")
    print(f"   Output length: {len(result['output'])} characters")
    print(f"   Validation passed: {result['validation_passed']}")

    # Get system status
    print("\n2. Getting system status...")
    status = client.get_status()
    print(f"   System health: {status['system_health']}")
    print(f"   Total optimizations: {status['total_optimizations']}")

    # Get version history
    print("\n3. Getting version history...")
    versions = client.get_versions()
    print(f"   Total versions: {len(versions)}")
    if versions:
        latest = versions[-1]
        print(f"   Latest version: {latest['version_id']}")


def example_graphql():
    """Example: Using GraphQL"""
    print("\n=== GraphQL Example ===\n")

    client = AutonomAIClient()

    # Get status via GraphQL
    print("1. Getting status via GraphQL...")
    status = client.graphql_get_status()
    print(f"   System health: {status['systemHealth']}")
    print(f"   Current version: {status['currentVersion']}")

    # Execute query via GraphQL
    print("\n2. Executing query via GraphQL mutation...")
    result = client.graphql_execute("What is artificial intelligence?")
    print(f"   Validation passed: {result['validationPassed']}")
    print(f"   Output length: {len(result['output'])} characters")

    # Get versions via GraphQL
    print("\n3. Getting versions via GraphQL...")
    versions = client.graphql_get_versions()
    print(f"   Total versions: {len(versions)}")


def example_webhooks():
    """Example: Managing webhooks"""
    print("\n=== Webhooks Example ===\n")

    client = AutonomAIClient()

    # Register a webhook
    print("1. Registering webhook...")
    webhook = client.register_webhook(
        url="https://example.com/webhook",
        events=["job_finished", "optimization_completed"],
        secret="my-secret-key",
    )
    print(f"   Webhook ID: {webhook['id']}")
    print(f"   Events: {webhook['events']}")

    webhook_id = webhook["id"]

    # List webhooks
    print("\n2. Listing all webhooks...")
    webhooks = client.list_webhooks()
    print(f"   Total webhooks: {len(webhooks)}")

    # Deactivate webhook
    print("\n3. Deactivating webhook...")
    client.deactivate_webhook(webhook_id)
    print("   Webhook deactivated")

    # Reactivate webhook
    print("\n4. Reactivating webhook...")
    client.activate_webhook(webhook_id)
    print("   Webhook reactivated")

    # Unregister webhook
    print("\n5. Unregistering webhook...")
    client.unregister_webhook(webhook_id)
    print("   Webhook unregistered")


async def example_websockets():
    """Example: Using WebSockets for real-time updates"""
    print("\n=== WebSockets Example ===\n")

    client = AutonomAIClient()

    async def on_job_update(data):
        """Callback for job updates"""
        if data.get("type") == "job_completed":
            print(f"   Job {data['job_id']} completed: {data['success']}")

    async def on_workflow_update(data):
        """Callback for workflow updates"""
        if data.get("type") == "workflow_update":
            print(
                f"   Workflow {data['workflow_id']} status: {data['status']}"
            )

    print("1. Listening to job updates (press Ctrl+C to stop)...")
    try:
        await asyncio.wait_for(
            client.listen_to_jobs(on_job_update), timeout=5.0
        )
    except asyncio.TimeoutError:
        print("   No job updates received (this is expected in demo)")


async def example_complete_workflow():
    """Example: Complete workflow using multiple features"""
    print("\n=== Complete Workflow Example ===\n")

    client = AutonomAIClient()

    # 1. Register webhook for notifications
    print("1. Setting up webhook...")
    webhook = client.register_webhook(
        url="https://example.com/webhook",
        events=["job_finished", "optimization_completed"],
    )
    print(f"   Webhook registered: {webhook['id']}")

    # 2. Start listening to WebSocket updates
    print("\n2. Starting WebSocket listener...")

    async def on_update(data):
        print(f"   WebSocket update: {data.get('type')}")

    # Start WebSocket listener in background
    ws_task = asyncio.create_task(
        asyncio.wait_for(client.listen_to_all(on_update), timeout=2.0)
    )

    # 3. Execute query (will trigger webhook and WebSocket notifications)
    print("\n3. Executing query...")
    result = client.execute_query("Explain neural networks")
    print(f"   Query executed: {result['validation_passed']}")

    # 4. Check status via GraphQL
    print("\n4. Checking status via GraphQL...")
    status = client.graphql_get_status()
    print(f"   System health: {status['systemHealth']}")

    # Wait for WebSocket updates
    try:
        await ws_task
    except asyncio.TimeoutError:
        print("   WebSocket timeout (expected in demo)")

    # 5. Cleanup
    print("\n5. Cleaning up...")
    client.unregister_webhook(webhook["id"])
    print("   Webhook unregistered")


def main():
    """Run all examples"""
    print("=" * 60)
    print("AutonomAI API v2 - Advanced Features Demo")
    print("=" * 60)

    # REST API examples
    try:
        example_rest_api()
    except Exception as e:
        print(f"REST API example failed: {e}")

    # GraphQL examples
    try:
        example_graphql()
    except Exception as e:
        print(f"GraphQL example failed: {e}")

    # Webhook examples
    try:
        example_webhooks()
    except Exception as e:
        print(f"Webhook example failed: {e}")

    # WebSocket examples
    try:
        asyncio.run(example_websockets())
    except Exception as e:
        print(f"WebSocket example failed: {e}")

    # Complete workflow example
    try:
        asyncio.run(example_complete_workflow())
    except Exception as e:
        print(f"Complete workflow example failed: {e}")

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
