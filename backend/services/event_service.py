# Glue: runs the repository save, then broadcasts through the WebSocket manager.

import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.repository import EventRepository, SourceRepository
from backend.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)


class EventService:
    """
    Orchestrates the two things that happen when a new security event arrives:
      1. Persist it to SQLite.
      2. Broadcast it to all connected WebSocket clients.

    If the database save fails, the WebSocket broadcast is skipped
    (don't broadcast an event we failed to store).

    If the WebSocket broadcast fails, the database record is unaffected.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def persist_and_broadcast(self, event_dict: dict) -> bool:
        """Save the event to the database, then push it to live dashboards."""
        try:
            await EventRepository.create(self._session, event_dict)
            await SourceRepository.upsert(self._session, event_dict['source_ip'], event_dict)
            await self._session.commit()

        except Exception as exc:
            logger.error('Failed to persist event %s: %s', event_dict.get('event_id'), exc)
            await self._session.rollback()
            return False

        # 4. Broadcast to WebSocket clients.
        # Failures here must never affect database integrity.
        try:
            ws_payload = {
                'type': 'security_event',
                'data': {
                    'event_id': event_dict['event_id'],
                    'source_ip': event_dict['source_ip'],
                    'timestamp': (
                        event_dict['timestamp'].isoformat()
                        if isinstance(event_dict['timestamp'], datetime)
                        else str(event_dict['timestamp'])
                    ),
                    'attack_category': event_dict['attack_category'],
                    'severity': event_dict['severity'],
                    'confidence': event_dict['confidence'],
                    'target': event_dict.get('target', '/'),
                    'method': event_dict.get('method', 'GET'),
                    'path': event_dict.get('path', '/'),
                    'detector_names': event_dict.get('detector_names', []),
                    'detection_reasons': event_dict.get('detection_reasons', []),
                },
            }
            await ws_manager.broadcast(ws_payload)
        except Exception as exc:
            logger.warning('WebSocket broadcast failed: %s', exc)
        return True
