# Tracks connected WebSocket clients and broadcasts events to them.

import json
import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Keeps track of all active WebSocket connections.

    When a new security event arrives, broadcast() sends it to
    every connected client. If one client's send fails, it is
    removed — this never prevents other clients from receiving the event.
    """

    def __init__(self):
        # Set of active WebSocket connections.
        self._connections: set = set()

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    async def connect(self, websocket: WebSocket):
        """Accept and register a new client."""
        await websocket.accept()
        self._connections.add(websocket)
        logger.info('WebSocket client connected. Total: %d', self.connection_count)

    def disconnect(self, websocket: WebSocket):
        """Remove a client (called on disconnect or error)."""
        self._connections.discard(websocket)
        logger.info('WebSocket client disconnected. Total: %d', self.connection_count)

    async def broadcast(self, message: dict):
        """
        Send a message to all connected clients.

        Failed sends are silently removed so they don't block other clients.
        """
        if not self._connections:
            return

        message_str = json.dumps(message, default=str)
        dead = set()

        for ws in list(self._connections):
            try:
                await ws.send_text(message_str)
            except Exception as exc:
                logger.debug('WebSocket send failed: %s', exc)
                dead.add(ws)

        # Clean up dead connections.
        for ws in dead:
            self._connections.discard(ws)


# Single shared instance used throughout the backend.
ws_manager = WebSocketManager()
