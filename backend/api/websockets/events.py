# /ws/events — WebSocket endpoint that streams new security events to dashboards.

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from backend.auth import authenticate_websocket
from backend.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket('/ws/events')
async def websocket_events(
    websocket: WebSocket,
    api_key: str = Query(None),
):
    cookie = websocket.headers.get('cookie')
    if not authenticate_websocket(api_key, cookie):
        await websocket.close(code=4001, reason='Invalid credentials')
        return

    await ws_manager.connect(websocket)
    try:
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                await websocket.send_json({'type': 'ping'})
            except WebSocketDisconnect:
                break
    except Exception as exc:
        logger.debug('WebSocket connection closed: %s', exc)
    finally:
        ws_manager.disconnect(websocket)
