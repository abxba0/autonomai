"""
Webhook management system for event notifications
"""

import asyncio
import hashlib
import hmac
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
import httpx
import logging

logger = logging.getLogger(__name__)


@dataclass
class Webhook:
    """Webhook registration"""

    id: str
    url: str
    events: Set[str]
    secret: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    active: bool = True
    retry_count: int = 3
    timeout: int = 30


@dataclass
class WebhookEvent:
    """Event to be sent to webhooks"""

    event_type: str
    data: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class WebhookManager:
    """Manages webhook registrations and event delivery"""

    def __init__(self):
        self.webhooks: Dict[str, Webhook] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self._delivery_task: Optional[asyncio.Task] = None
        self._running = False

    def register_webhook(
        self, url: str, events: List[str], secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register a new webhook"""
        webhook_id = str(uuid.uuid4())
        webhook = Webhook(
            id=webhook_id, url=url, events=set(events), secret=secret
        )
        self.webhooks[webhook_id] = webhook

        logger.info(f"Registered webhook {webhook_id} for events: {events}")

        return {
            "id": webhook.id,
            "url": webhook.url,
            "events": list(webhook.events),
            "created_at": webhook.created_at,
            "active": webhook.active,
        }

    def unregister_webhook(self, webhook_id: str) -> bool:
        """Unregister a webhook"""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            logger.info(f"Unregistered webhook {webhook_id}")
            return True
        return False

    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List all registered webhooks"""
        return [
            {
                "id": w.id,
                "url": w.url,
                "events": list(w.events),
                "created_at": w.created_at,
                "active": w.active,
            }
            for w in self.webhooks.values()
        ]

    def deactivate_webhook(self, webhook_id: str) -> bool:
        """Deactivate a webhook without unregistering it"""
        if webhook_id in self.webhooks:
            self.webhooks[webhook_id].active = False
            logger.info(f"Deactivated webhook {webhook_id}")
            return True
        return False

    def activate_webhook(self, webhook_id: str) -> bool:
        """Activate a previously deactivated webhook"""
        if webhook_id in self.webhooks:
            self.webhooks[webhook_id].active = True
            logger.info(f"Activated webhook {webhook_id}")
            return True
        return False

    async def trigger_event(self, event_type: str, data: Dict[str, Any]):
        """Trigger an event to be sent to subscribed webhooks"""
        event = WebhookEvent(event_type=event_type, data=data)
        await self.event_queue.put(event)
        logger.debug(f"Queued event: {event_type}")

    def _generate_signature(self, payload: bytes, secret: str) -> str:
        """Generate HMAC signature for webhook payload"""
        return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    async def _deliver_webhook(
        self, webhook: Webhook, event: WebhookEvent
    ) -> bool:
        """Deliver an event to a specific webhook with retry logic"""
        payload = {
            "event": event.event_type,
            "data": event.data,
            "timestamp": event.timestamp,
            "webhook_id": webhook.id,
        }

        payload_bytes = json.dumps(payload).encode()
        headers = {"Content-Type": "application/json"}

        if webhook.secret:
            signature = self._generate_signature(payload_bytes, webhook.secret)
            headers["X-Webhook-Signature"] = signature

        for attempt in range(webhook.retry_count):
            try:
                async with httpx.AsyncClient(timeout=webhook.timeout) as client:
                    response = await client.post(
                        webhook.url, content=payload_bytes, headers=headers
                    )

                    if response.status_code == 200:
                        logger.info(
                            f"Successfully delivered event {event.event_type} to webhook {webhook.id}"
                        )
                        return True
                    else:
                        logger.warning(
                            f"Webhook {webhook.id} returned status {response.status_code}, "
                            f"attempt {attempt + 1}/{webhook.retry_count}"
                        )

            except Exception as e:
                logger.error(
                    f"Error delivering to webhook {webhook.id}, "
                    f"attempt {attempt + 1}/{webhook.retry_count}: {e}"
                )

            # Wait before retry (exponential backoff)
            if attempt < webhook.retry_count - 1:
                await asyncio.sleep(2 ** attempt)

        # All retries failed - deactivate webhook
        logger.error(
            f"Failed to deliver event to webhook {webhook.id} after {webhook.retry_count} attempts. "
            "Deactivating webhook."
        )
        self.deactivate_webhook(webhook.id)
        return False

    async def _process_events(self):
        """Background task to process webhook events"""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self.event_queue.get(), timeout=1.0
                )

                # Find webhooks subscribed to this event
                subscribed_webhooks = [
                    w
                    for w in self.webhooks.values()
                    if w.active and event.event_type in w.events
                ]

                if subscribed_webhooks:
                    # Deliver to all subscribed webhooks in parallel
                    tasks = [
                        self._deliver_webhook(webhook, event)
                        for webhook in subscribed_webhooks
                    ]
                    await asyncio.gather(*tasks, return_exceptions=True)
                else:
                    logger.debug(f"No active webhooks for event: {event.event_type}")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing webhook event: {e}")

    def start(self):
        """Start the webhook delivery background task"""
        if not self._running:
            self._running = True
            # Note: Task should be started in an async context
            logger.info("Webhook manager ready (call start_async in event loop)")

    async def start_async(self):
        """Start the webhook delivery task in an async context"""
        if not self._delivery_task or self._delivery_task.done():
            self._running = True
            self._delivery_task = asyncio.create_task(self._process_events())
            logger.info("Webhook delivery task started")

    async def stop(self):
        """Stop the webhook delivery background task"""
        self._running = False
        if self._delivery_task:
            self._delivery_task.cancel()
            try:
                await self._delivery_task
            except asyncio.CancelledError:
                pass
            logger.info("Webhook delivery task stopped")


# Singleton instance
_webhook_manager_instance = None


def get_webhook_manager() -> WebhookManager:
    """Get or create webhook manager singleton"""
    global _webhook_manager_instance
    if _webhook_manager_instance is None:
        _webhook_manager_instance = WebhookManager()
        _webhook_manager_instance.start()
    return _webhook_manager_instance
