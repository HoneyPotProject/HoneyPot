# EngineAdapter: owns the asyncio.Queue, creates BackendEventSink,
# and runs the EventWorker task that drains the queue to the database.

import asyncio
import logging
import time

from backend.integration.event_mapper import to_db_dict
from backend.integration.event_sink import BackendEventSink

logger = logging.getLogger(__name__)


class EngineAdapter:
    """
    Ties the detection engine to the backend storage pipeline.

    Lifecycle:
      1. Instantiated once at application startup.
      2. start() creates the queue, the sink, and starts the worker task.
      3. The engine writes events via sink.save().
      4. The worker reads from the queue and calls EventService.
      5. stop() drains the queue and cancels the worker.

    QUEUE LIMITATION (documented):
      The queue is in-memory only. Events in the queue at crash time are lost.
      This is acceptable for the initial development version.
    """

    def __init__(self, queue_size: int = 1000):
        self._queue_size = queue_size
        self._queue: asyncio.Queue = None
        self._sink: BackendEventSink = None
        self._worker_task: asyncio.Task = None
        self._dropped = [0]
        self._errors = [0]
        self._processed = [0]
        self._last_event_id: str | None = None
        self._start_time = time.time()

    def start(self, session_factory) -> BackendEventSink:
        """
        Create the queue, sink, and start the worker.

        Returns the BackendEventSink so it can be passed to EventProcessor.
        session_factory is a callable that returns an AsyncSession context.
        """
        self._queue = asyncio.Queue(maxsize=self._queue_size)
        self._dropped = [0]
        self._errors = [0]
        self._processed = [0]
        self._last_event_id = None
        self._sink = BackendEventSink(self._queue, self._dropped)
        self._worker_task = asyncio.create_task(
            self._worker_loop(session_factory),
            name='event-worker',
        )
        logger.info('EngineAdapter started. Queue capacity: %d', self._queue_size)
        return self._sink

    async def stop(self):
        """Gracefully drain the queue and cancel the worker."""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info(
            'EngineAdapter stopped. Dropped=%d Errors=%d',
            self._dropped[0], self._errors[0]
        )

    @property
    def queue_depth(self) -> int:
        return self._queue.qsize() if self._queue else 0

    @property
    def dropped_events(self) -> int:
        return self._dropped[0]

    @property
    def processing_errors(self) -> int:
        return self._errors[0]

    @property
    def processed_events(self) -> int:
        return self._processed[0]

    @property
    def last_processed_event(self) -> str | None:
        return self._last_event_id

    @property
    def uptime_seconds(self) -> float:
        return round(time.time() - self._start_time, 1)

    @property
    def queue_capacity(self) -> int:
        return self._queue_size

    async def _worker_loop(self, session_factory):
        """
        Continuously read events from the queue and persist them.

        Flow per event:
          queue.get() -> to_db_dict() -> EventService.persist_and_broadcast()
        """
        from backend.services.event_service import EventService

        while True:
            try:
                # Wait until an event is available.
                engine_event = await self._queue.get()

                # Convert engine object to plain dict.
                event_dict = to_db_dict(engine_event)

                # Persist and broadcast using a fresh DB session.
                async with session_factory() as session:
                    service = EventService(session)
                    saved = await service.persist_and_broadcast(event_dict)

                if saved:
                    self._processed[0] += 1
                    self._last_event_id = event_dict.get('event_id')
                else:
                    self._errors[0] += 1
                self._queue.task_done()

            except asyncio.CancelledError:
                # Graceful shutdown.
                break
            except Exception as exc:
                self._errors[0] += 1
                logger.error('EventWorker error: %s', exc, exc_info=True)
                # Continue running — one failure must not kill the worker.
