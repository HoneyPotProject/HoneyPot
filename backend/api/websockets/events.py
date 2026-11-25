# /ws/events — WebSocket endpoint that streams new security events to dashboards.

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from backend.config import settings
from backend.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket('/ws/events')
async def websocket_events(
    websocket: WebSocket,
    api_key: str = Query(None),
):
    """
    WebSocket endpoint for live event streaming.

    Clients authenticate by passing ?api_key=<key> in the URL.

    After connecting, clients receive JSON messages whenever a new
    security event is detected. Message format:
      {"type": "security_event", "data": { ... }}

    A heartbeat ping is sent every 30 seconds to keep the connection alive.
    """
    # Authenticate the WebSocket client.
    if api_key != settings.API_KEY:
        await websocket.close(code=4001, reason='Invalid API key')
        return

    # Register the connection.
    await ws_manager.connect(websocket)

    try:
        # Keep the connection alive: handle incoming messages
        # and send periodic heartbeats.
        while True:
            try:
                # Wait for a client message or timeout.
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send a heartbeat ping so the browser keeps the connection.
                await websocket.send_json({'type': 'ping'})
            except WebSocketDisconnect:
                break
    except Exception as exc:
        logger.debug('WebSocket connection closed: %s', exc)
    finally:
        ws_manager.disconnect(websocket)
