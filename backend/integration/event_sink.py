# BackendEventSink: accepts SecurityEvent objects from the engine and
# puts them into the bounded asyncio queue for the event worker.

import asyncio
import logging

# The engine's abstract interface (the only cross-module import from engine).
from engine.events.storage_interface import EventSink
from engine.events.event import SecurityEvent

logger = logging.getLogger(__name__)


class BackendEventSink(EventSink):
    """
    Concrete EventSink implementation used in production.

    When the engine calls save(event), this class puts the event
    into the bounded asyncio.Queue. The EventWorker reads from
    that queue and handles persistence + WebSocket broadcast.

    DEPENDENCY DIRECTION:
      This class imports from engine/ (the abstract interface).
      engine/ never imports from backend/.
    """

    def __init__(self, queue: asyncio.Queue, dropped_counter: list):
        # The bounded queue shared with the EventWorker.
        self._queue = queue
        # Mutable list[int] so we can increment the counter across references.
        # dropped_counter[0] is the count.
        self._dropped = dropped_counter

    async def save(self, event: SecurityEvent) -> None:
        """
        Put the event into the queue.

        If the queue is full, the event is dropped and counted.
        This method must NEVER raise — it is called from inside the detection engine.
        """
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            self._dropped[0] += 1
            logger.warning(
                'Event queue full — event dropped. event_id=%s source_ip=%s dropped_total=%d',
                str(event.event_id),
                event.source_ip,
                self._dropped[0],
            )
        except Exception as exc:
            # Catch-all: the engine must keep running even if something unexpected happens.
            logger.error('Unexpected error in BackendEventSink.save(): %s', exc)
