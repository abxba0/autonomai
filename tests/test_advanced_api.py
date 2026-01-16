"""
Tests for advanced API features: GraphQL, WebSockets, Webhooks, and Versioning
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Test webhook manager
from web.webhook_manager import WebhookManager, Webhook, WebhookEvent


class TestWebhookManager:
    """Test webhook management system"""

    def setup_method(self):
        """Setup test fixtures"""
        self.manager = WebhookManager()

    def test_register_webhook(self):
        """Test webhook registration"""
        webhook = self.manager.register_webhook(
            url="https://example.com/webhook",
            events=["job_finished", "optimization_completed"],
            secret="test_secret",
        )

        assert webhook["id"] is not None
        assert webhook["url"] == "https://example.com/webhook"
        assert set(webhook["events"]) == {"job_finished", "optimization_completed"}
        assert webhook["active"] is True

    def test_list_webhooks(self):
        """Test listing webhooks"""
        # Register multiple webhooks
        self.manager.register_webhook(
            url="https://example.com/webhook1", events=["job_finished"]
        )
        self.manager.register_webhook(
            url="https://example.com/webhook2", events=["optimization_completed"]
        )

        webhooks = self.manager.list_webhooks()
        assert len(webhooks) == 2

    def test_unregister_webhook(self):
        """Test webhook unregistration"""
        webhook = self.manager.register_webhook(
            url="https://example.com/webhook", events=["job_finished"]
        )

        success = self.manager.unregister_webhook(webhook["id"])
        assert success is True

        webhooks = self.manager.list_webhooks()
        assert len(webhooks) == 0

    def test_deactivate_webhook(self):
        """Test webhook deactivation"""
        webhook = self.manager.register_webhook(
            url="https://example.com/webhook", events=["job_finished"]
        )

        success = self.manager.deactivate_webhook(webhook["id"])
        assert success is True

        webhooks = self.manager.list_webhooks()
        assert webhooks[0]["active"] is False

    def test_activate_webhook(self):
        """Test webhook activation"""
        webhook = self.manager.register_webhook(
            url="https://example.com/webhook", events=["job_finished"]
        )

        self.manager.deactivate_webhook(webhook["id"])
        success = self.manager.activate_webhook(webhook["id"])
        assert success is True

        webhooks = self.manager.list_webhooks()
        assert webhooks[0]["active"] is True

    @pytest.mark.asyncio
    async def test_trigger_event(self):
        """Test event triggering"""
        await self.manager.trigger_event(
            "job_finished", {"job_id": "test123", "success": True}
        )

        # Event should be in queue
        assert not self.manager.event_queue.empty()

    def test_generate_signature(self):
        """Test signature generation"""
        payload = b'{"test": "data"}'
        secret = "test_secret"

        signature1 = self.manager._generate_signature(payload, secret)
        signature2 = self.manager._generate_signature(payload, secret)

        # Same payload and secret should generate same signature
        assert signature1 == signature2

        # Different payloads should generate different signatures
        different_payload = b'{"test": "different"}'
        signature3 = self.manager._generate_signature(different_payload, secret)
        assert signature1 != signature3


# Test WebSocket connection manager
from web.websocket_handlers import ConnectionManager


class MockWebSocket:
    """Mock WebSocket for testing"""

    def __init__(self):
        self.accepted = False
        self.messages = []
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def send_json(self, data):
        if not self.closed:
            self.messages.append(data)
        else:
            raise Exception("WebSocket closed")

    async def receive_text(self):
        # Simulate receiving a message
        return json.dumps({"type": "ping"})


class TestConnectionManager:
    """Test WebSocket connection manager"""

    def setup_method(self):
        """Setup test fixtures"""
        self.manager = ConnectionManager()

    @pytest.mark.asyncio
    async def test_connect(self):
        """Test WebSocket connection"""
        ws = MockWebSocket()
        await self.manager.connect(ws)

        assert ws.accepted is True
        assert ws in self.manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test WebSocket disconnection"""
        ws = MockWebSocket()
        await self.manager.connect(ws)

        self.manager.disconnect(ws)
        assert ws not in self.manager.active_connections

    @pytest.mark.asyncio
    async def test_send_personal_message(self):
        """Test sending personal message"""
        ws = MockWebSocket()
        await self.manager.connect(ws)

        message = {"type": "test", "data": "hello"}
        await self.manager.send_personal_message(message, ws)

        assert len(ws.messages) == 1
        assert ws.messages[0] == message

    @pytest.mark.asyncio
    async def test_broadcast(self):
        """Test broadcasting to all connections"""
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await self.manager.connect(ws1)
        await self.manager.connect(ws2)

        message = {"type": "broadcast", "data": "hello all"}
        await self.manager.broadcast(message)

        assert len(ws1.messages) == 1
        assert len(ws2.messages) == 1
        assert ws1.messages[0] == message
        assert ws2.messages[0] == message

    @pytest.mark.asyncio
    async def test_subscribe_to_channel(self):
        """Test channel subscription"""
        ws = MockWebSocket()
        await self.manager.connect(ws)

        await self.manager.subscribe(ws, "workflows")
        assert "workflows" in self.manager.subscriptions
        assert ws in self.manager.subscriptions["workflows"]

    @pytest.mark.asyncio
    async def test_broadcast_to_channel(self):
        """Test broadcasting to specific channel"""
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await self.manager.connect(ws1)
        await self.manager.connect(ws2)

        await self.manager.subscribe(ws1, "workflows")
        await self.manager.subscribe(ws2, "jobs")

        message = {"type": "workflow_update", "data": "test"}
        await self.manager.broadcast_to_channel("workflows", message)

        # Only ws1 should receive the message
        assert len(ws1.messages) == 1
        assert len(ws2.messages) == 0
        assert ws1.messages[0] == message

    @pytest.mark.asyncio
    async def test_unsubscribe_from_channel(self):
        """Test channel unsubscription"""
        ws = MockWebSocket()
        await self.manager.connect(ws)

        await self.manager.subscribe(ws, "workflows")
        await self.manager.unsubscribe(ws, "workflows")

        assert ws not in self.manager.subscriptions["workflows"]


# Test GraphQL schema
class TestGraphQLSchema:
    """Test GraphQL schema and resolvers"""

    def test_schema_types(self):
        """Test that schema types are properly defined"""
        from web.graphql_schema import schema

        # Check that schema is created
        assert schema is not None

        # Check query type
        assert schema.query_type is not None

        # Check mutation type
        assert schema.mutation_type is not None

    def test_validation_result_type(self):
        """Test ValidationResult type"""
        from web.graphql_schema import ValidationResult

        result = ValidationResult(
            validator_name="test_validator",
            passed=True,
            error_message=None,
        )

        assert result.validator_name == "test_validator"
        assert result.passed is True
        assert result.error_message is None

    def test_webhook_info_type(self):
        """Test WebhookInfo type"""
        from web.graphql_schema import WebhookInfo

        webhook = WebhookInfo(
            id="test_id",
            url="https://example.com",
            events=["job_finished"],
            created_at=datetime.now().isoformat(),
            active=True,
        )

        assert webhook.id == "test_id"
        assert webhook.url == "https://example.com"
        assert "job_finished" in webhook.events


# Test API versioning
class TestAPIVersioning:
    """Test API versioning functionality"""

    def test_version_constants(self):
        """Test version constants are defined"""
        from web.api_v2 import (
            API_VERSION_V1,
            API_VERSION_V2,
            CURRENT_VERSION,
            DEPRECATED_VERSIONS,
        )

        assert API_VERSION_V1 == "v1"
        assert API_VERSION_V2 == "v2"
        assert CURRENT_VERSION == "v2"
        assert "v1" in DEPRECATED_VERSIONS

    def test_pydantic_models(self):
        """Test Pydantic models for API requests/responses"""
        from web.api_v2 import ExecuteRequest, ExecuteResponse, WebhookRegisterRequest

        # Test ExecuteRequest
        request = ExecuteRequest(query="test query")
        assert request.query == "test query"
        assert request.conversation_context is None

        # Test WebhookRegisterRequest
        webhook_req = WebhookRegisterRequest(
            url="https://example.com", events=["job_finished"]
        )
        assert webhook_req.url == "https://example.com"
        assert "job_finished" in webhook_req.events


# Integration tests
class TestAPIIntegration:
    """Integration tests for API features"""

    @pytest.mark.asyncio
    async def test_webhook_event_flow(self):
        """Test complete webhook event flow"""
        manager = WebhookManager()

        # Register webhook
        webhook = manager.register_webhook(
            url="https://example.com/webhook",
            events=["job_finished"],
        )

        # Trigger event
        await manager.trigger_event(
            "job_finished",
            {"job_id": "test123", "success": True},
        )

        # Event should be queued
        assert not manager.event_queue.empty()

    @pytest.mark.asyncio
    async def test_websocket_notification_flow(self):
        """Test WebSocket notification flow"""
        from web.websocket_handlers import (
            notify_job_completed,
            notify_optimization_completed,
        )

        # These should not raise errors even if no connections exist
        await notify_job_completed(
            job_id="test123",
            success=True,
            result={"output": "test"},
        )

        await notify_optimization_completed(
            version_id="v1",
            changes={"rules_added": 1},
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
