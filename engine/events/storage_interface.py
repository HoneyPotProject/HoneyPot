# An abstract EventSink with save(event). The backend provides the SQLite
# implementation and tests provide an in-memory one.

from __future__ import annotations

import abc

from engine.events.event import SecurityEvent


class EventSink(abc.ABC):
    """
    Integration boundary between the detection engine and storage.

    The engine never imports backend modules. Concrete sinks live in
    backend/integration or in tests.
    """

    @abc.abstractmethod
    async def save(self, event: SecurityEvent) -> None:
        """Persist or forward a security event without blocking detection."""
        raise NotImplementedError
