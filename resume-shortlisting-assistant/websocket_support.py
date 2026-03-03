"""
WebSocket Support for Real-time Updates.

This module provides WebSocket functionality for real-time feedback during
long-running operations like PDF processing and resume evaluation.

Features:
- Real-time task progress updates
- Live candidate status notifications
- Broadcast capabilities for admin dashboard
- Connection management and cleanup
- Integration with task queue system

Usage:
    from websocket_support import WebSocketManager, progress_update

    ws_manager = WebSocketManager()

    @app.route('/ws')
    def websocket_endpoint(websocket):
        await ws_manager.connect(websocket)

Contributor: shubham21155102
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WebSocket message types."""
    # Task updates
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"

    # Candidate updates
    CANDIDATE_CREATED = "candidate_created"
    CANDIDATE_UPDATED = "candidate_updated"
    CANDIDATE_DELETED = "candidate_deleted"

    # System messages
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    INFO = "info"


@dataclass
class WebSocketMessage:
    """Structure for WebSocket messages."""
    type: MessageType
    data: Dict[str, Any]
    timestamp: str = None
    request_id: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps({
            'type': self.type.value,
            'data': self.data,
            'timestamp': self.timestamp,
            'request_id': self.request_id
        })


class WebSocketConnection:
    """Represents a WebSocket connection with metadata."""

    def __init__(self, ws, client_id: str, subscribed_channels: Set[str] = None):
        """
        Initialize WebSocket connection.

        Args:
            ws: WebSocket instance
            client_id: Unique client identifier
            subscribed_channels: Set of channels to subscribe to
        """
        self.ws = ws
        self.client_id = client_id
        self.subscribed_channels = subscribed_channels or {'general'}
        self.connected_at = datetime.now()
        self.last_ping = datetime.now()

    async def send(self, message: WebSocketMessage):
        """Send a message to this connection."""
        try:
            await self.ws.send(message.to_json())
        except Exception as e:
            logger.error(f"Error sending to client {self.client_id}: {e}")


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts.

    This is a simplified implementation using asyncio.
    For production with multiple workers, use Redis pub/sub.
    """

    def __init__(self):
        """Initialize the WebSocket manager."""
        self.connections: Dict[str, WebSocketConnection] = {}
        self.channel_subscribers: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, ws, client_id: str, channels: Set[str] = None) -> WebSocketConnection:
        """
        Register a new WebSocket connection.

        Args:
            ws: WebSocket instance
            client_id: Unique client identifier
            channels: Channels to subscribe to

        Returns:
            WebSocketConnection instance
        """
        async with self._lock:
            connection = WebSocketConnection(ws, client_id, channels)
            self.connections[client_id] = connection

            # Register channel subscriptions
            for channel in connection.subscribed_channels:
                if channel not in self.channel_subscribers:
                    self.channel_subscribers[channel] = set()
                self.channel_subscribers[channel].add(client_id)

            logger.info(f"Client {client_id} connected. Subscribed to: {channels}")

            # Send welcome message
            await connection.send(WebSocketMessage(
                type=MessageType.INFO,
                data={'message': 'Connected to AI Recruit WebSocket'}
            ))

            return connection

    async def disconnect(self, client_id: str):
        """
        Unregister a WebSocket connection.

        Args:
            client_id: Client identifier to disconnect
        """
        async with self._lock:
            connection = self.connections.pop(client_id, None)
            if connection:
                # Remove from channel subscriptions
                for channel in connection.subscribed_channels:
                    if channel in self.channel_subscribers:
                        self.channel_subscribers[channel].discard(client_id)

                logger.info(f"Client {client_id} disconnected")

    async def send_to_client(self, client_id: str, message: WebSocketMessage):
        """
        Send a message to a specific client.

        Args:
            client_id: Client identifier
            message: Message to send
        """
        connection = self.connections.get(client_id)
        if connection:
            await connection.send(message)

    async def broadcast(self, message: WebSocketMessage, channel: str = 'general'):
        """
        Broadcast a message to all subscribers of a channel.

        Args:
            message: Message to broadcast
            channel: Channel to broadcast to (default: 'general')
        """
        async with self._lock:
            subscribers = self.channel_subscribers.get(channel, set())

        # Send to all subscribers
        tasks = []
        for client_id in subscribers:
            tasks.append(self.send_to_client(client_id, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.debug(f"Broadcast to {len(tasks)} clients on channel '{channel}'")

    async def broadcast_all(self, message: WebSocketMessage):
        """
        Broadcast a message to all connected clients.

        Args:
            message: Message to broadcast
        """
        async with self._lock:
            client_ids = list(self.connections.keys())

        tasks = [self.send_to_client(cid, message) for cid in client_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get connection statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            'total_connections': len(self.connections),
            'channels': {
                channel: len(subscribers)
                for channel, subscribers in self.channel_subscribers.items()
            }
        }


# =============================================================================
# Convenience Functions for Task Updates
# =============================================================================

_global_ws_manager: Optional[WebSocketManager] = None


def get_ws_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    global _global_ws_manager
    if _global_ws_manager is None:
        _global_ws_manager = WebSocketManager()
    return _global_ws_manager


async def send_task_update(task_id: str, status: str, progress: int = None, **extra_data):
    """
    Send a task update to all subscribers.

    Args:
        task_id: Task identifier
        status: Task status
        progress: Progress percentage (0-100) if applicable
        **extra_data: Additional data to include
    """
    manager = get_ws_manager()

    message_type = {
        'created': MessageType.TASK_CREATED,
        'started': MessageType.TASK_STARTED,
        'processing': MessageType.TASK_PROGRESS,
        'completed': MessageType.TASK_COMPLETED,
        'failed': MessageType.TASK_FAILED,
    }.get(status, MessageType.INFO)

    data = {
        'task_id': task_id,
        'status': status,
        **extra_data
    }

    if progress is not None:
        data['progress'] = progress

    message = WebSocketMessage(type=message_type, data=data)
    await manager.broadcast(message, channel='tasks')


async def send_candidate_update(candidate_id: int, action: str, **extra_data):
    """
    Send a candidate update notification.

    Args:
        candidate_id: Candidate database ID
        action: Action performed (created, updated, deleted)
        **extra_data: Additional data
    """
    manager = get_ws_manager()

    message_type = {
        'created': MessageType.CANDIDATE_CREATED,
        'updated': MessageType.CANDIDATE_UPDATED,
        'deleted': MessageType.CANDIDATE_DELETED,
    }.get(action, MessageType.INFO)

    message = WebSocketMessage(
        type=message_type,
        data={'candidate_id': candidate_id, 'action': action, **extra_data}
    )
    await manager.broadcast(message, channel='candidates')


# =============================================================================
# Flask Integration (using flask-sock)
# =============================================================================

def init_websocket_support(app):
    """
    Initialize WebSocket support for a Flask app.

    This sets up the WebSocket routes using flask-sock.

    Args:
        app: Flask application instance

    Returns:
        WebSocket manager instance
    """
    try:
        from flask_sock import Sock
        from flask import request

        sock = Sock(app)
        manager = get_ws_manager()

        @sock.route('/ws')
        async def websocket_connection(ws):
            """Handle WebSocket connections."""
            client_id = request.args.get('client_id') or f"client_{id(ws)}"
            channels = set(request.args.getlist('channels')) or {'general'}

            connection = await manager.connect(ws, client_id, channels)

            try:
                # Keep connection alive and handle incoming messages
                async for message in ws:
                    try:
                        data = json.loads(message)
                        # Handle ping/pong for keepalive
                        if data.get('type') == 'ping':
                            await ws.send(json.dumps({'type': 'pong'}))
                        connection.last_ping = datetime.now()
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from client {client_id}")
            except Exception as e:
                logger.error(f"WebSocket error for {client_id}: {e}")
            finally:
                await manager.disconnect(client_id)

        logger.info("WebSocket support initialized")
        return manager

    except ImportError:
        logger.warning("flask-sock not installed. WebSocket support disabled.")
        return None


# =============================================================================
# Helper: Task Queue Integration
# =============================================================================

async def monitor_task_queue():
    """
    Background task to monitor the task queue and send WebSocket updates.

    This should be run as a background task to periodically check
    task status and broadcast updates to connected clients.
    """
    from task_queue import get_task_queue

    manager = get_ws_manager()
    queue = get_task_queue()

    last_checked_tasks = set()

    while True:
        try:
            await asyncio.sleep(1)  # Check every second

            stats = queue.get_statistics()

            # Send statistics update
            await manager.broadcast(WebSocketMessage(
                type=MessageType.INFO,
                data={'type': 'queue_stats', 'stats': stats}
            ), channel='system')

            # Check for completed tasks
            current_tasks = set(queue.tasks.keys())
            new_tasks = current_tasks - last_checked_tasks
            completed_tasks = [
                tid for tid in new_tasks
                if queue.tasks[tid].status == TaskStatus.COMPLETED
            ]

            for task_id in completed_tasks:
                task = queue.tasks[task_id]
                await send_task_update(
                    task_id=task_id,
                    status='completed',
                    result=task.result
                )

            last_checked_tasks = current_tasks

        except Exception as e:
            logger.error(f"Error in task queue monitor: {e}")
            await asyncio.sleep(5)


# =============================================================================
# SSE Alternative (Server-Sent Events)
# =============================================================================

class SSEManager:
    """
    Server-Sent Events manager as an alternative to WebSockets.

    SSE is simpler for one-way communication from server to client.
    """

    def __init__(self):
        """Initialize the SSE manager."""
        self.clients: Dict[str, asyncio.Queue] = {}

    async def subscribe(self, client_id: str) -> asyncio.Queue:
        """
        Subscribe a client to SSE updates.

        Args:
            client_id: Client identifier

        Returns:
            Queue for sending events to this client
        """
        queue = asyncio.Queue()
        self.clients[client_id] = queue
        return queue

    async def unsubscribe(self, client_id: str):
        """
        Unsubscribe a client from SSE updates.

        Args:
            client_id: Client identifier
        """
        self.clients.pop(client_id, None)

    async def broadcast(self, event: str, data: Dict[str, Any]):
        """
        Broadcast an event to all subscribed clients.

        Args:
            event: Event name
            data: Event data
        """
        message = f"event: {event}\ndata: {json.dumps(data)}\n\n"

        for client_id, queue in self.clients.items():
            try:
                await queue.put(message)
            except Exception as e:
                logger.error(f"Error sending SSE to {client_id}: {e}")

    def format_sse(self, event: str, data: Dict[str, Any]) -> str:
        """
        Format an SSE message.

        Args:
            event: Event name
            data: Event data

        Returns:
            Formatted SSE message string
        """
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"
