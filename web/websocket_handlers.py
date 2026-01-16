"""
WebSocket handlers for real-time updates
"""

import asyncio
import json
from typing import Set, Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscriptions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channels: Optional[list] = None):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)

        # Subscribe to channels if specified
        if channels:
            for channel in channels:
                if channel not in self.subscriptions:
                    self.subscriptions[channel] = set()
                self.subscriptions[channel].add(websocket)

        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.discard(websocket)

        # Remove from all subscriptions
        for channel_connections in self.subscriptions.values():
            channel_connections.discard(websocket)

        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """Broadcast a message to all clients subscribed to a specific channel"""
        if channel not in self.subscriptions:
            return

        disconnected = []
        for connection in self.subscriptions[channel]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to channel {channel}: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def subscribe(self, websocket: WebSocket, channel: str):
        """Subscribe a connection to a channel"""
        if channel not in self.subscriptions:
            self.subscriptions[channel] = set()
        self.subscriptions[channel].add(websocket)
        logger.info(f"WebSocket subscribed to channel: {channel}")

    async def unsubscribe(self, websocket: WebSocket, channel: str):
        """Unsubscribe a connection from a channel"""
        if channel in self.subscriptions:
            self.subscriptions[channel].discard(websocket)
            logger.info(f"WebSocket unsubscribed from channel: {channel}")


# Singleton instance
_connection_manager = None


def get_connection_manager() -> ConnectionManager:
    """Get or create connection manager singleton"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


async def handle_websocket_commands(websocket: WebSocket, connection_manager: ConnectionManager):
    """Handle commands received from WebSocket clients"""
    try:
        while True:
            data = await websocket.receive_text()
            try:
                command = json.loads(data)
                command_type = command.get("type")

                if command_type == "subscribe":
                    channel = command.get("channel")
                    if channel:
                        await connection_manager.subscribe(websocket, channel)
                        await connection_manager.send_personal_message(
                            {"type": "subscribed", "channel": channel}, websocket
                        )

                elif command_type == "unsubscribe":
                    channel = command.get("channel")
                    if channel:
                        await connection_manager.unsubscribe(websocket, channel)
                        await connection_manager.send_personal_message(
                            {"type": "unsubscribed", "channel": channel}, websocket
                        )

                elif command_type == "ping":
                    await connection_manager.send_personal_message(
                        {"type": "pong", "timestamp": command.get("timestamp")}, websocket
                    )

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                await connection_manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON"}, websocket
                )

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error handling WebSocket commands: {e}")
        connection_manager.disconnect(websocket)


async def notify_workflow_update(
    workflow_id: str,
    status: str,
    step: Optional[str] = None,
    message: Optional[str] = None
):
    """Notify clients about workflow status updates"""
    connection_manager = get_connection_manager()
    update = {
        "type": "workflow_update",
        "workflow_id": workflow_id,
        "status": status,
        "step": step,
        "message": message,
        "timestamp": asyncio.get_event_loop().time(),
    }
    await connection_manager.broadcast_to_channel("workflows", update)


async def notify_job_completed(
    job_id: str,
    success: bool,
    result: Optional[Dict[str, Any]] = None
):
    """Notify clients about job completion"""
    connection_manager = get_connection_manager()
    notification = {
        "type": "job_completed",
        "job_id": job_id,
        "success": success,
        "result": result,
        "timestamp": asyncio.get_event_loop().time(),
    }
    await connection_manager.broadcast_to_channel("jobs", notification)


async def notify_optimization_completed(
    version_id: str,
    changes: Dict[str, Any]
):
    """Notify clients about optimization completion"""
    connection_manager = get_connection_manager()
    notification = {
        "type": "optimization_completed",
        "version_id": version_id,
        "changes": changes,
        "timestamp": asyncio.get_event_loop().time(),
    }
    await connection_manager.broadcast_to_channel("optimizations", notification)


async def notify_regression_detected(
    metric: str,
    old_value: float,
    new_value: float,
    severity: str
):
    """Notify clients about regression detection"""
    connection_manager = get_connection_manager()
    alert = {
        "type": "regression_detected",
        "metric": metric,
        "old_value": old_value,
        "new_value": new_value,
        "severity": severity,
        "timestamp": asyncio.get_event_loop().time(),
    }
    await connection_manager.broadcast_to_channel("regressions", alert)
