# Parses the raw request, calls the collector, runs the engine, passes
# results to the processor, then asks the simulator for a response.

from __future__ import annotations

import asyncio
import logging

from engine.collectors.request_collector import RequestCollector
from engine.core.config import DEFAULT_CONFIG, EngineConfig
from engine.core.engine import DetectionEngine
from engine.events.event_processor import EventProcessor
from engine.server.response_simulator import encode_http, simulate

logger = logging.getLogger(__name__)


class RequestHandler:
    def __init__(
        self,
        collector: RequestCollector,
        engine: DetectionEngine,
        processor: EventProcessor,
        config: EngineConfig | None = None,
    ) -> None:
        self._collector = collector
        self._engine = engine
        self._processor = processor
        self._config = config or DEFAULT_CONFIG

    async def handle(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        peer = writer.get_extra_info('peername') or ('0.0.0.0', 0)
        source_ip = peer[0] if peer else '0.0.0.0'
        source_port = int(peer[1]) if peer and len(peer) > 1 else 0
        try:
            raw = await asyncio.wait_for(
                reader.read(self._config.max_request_bytes),
                timeout=self._config.request_timeout_seconds,
            )
            if not raw:
                return
            ctx = self._collector.collect(raw, source_ip, source_port)
            results = self._engine.analyze(ctx)
            await self._processor.process(ctx, results)
            status, body, content_type = simulate(ctx)
            writer.write(encode_http(status, body, content_type))
            await writer.drain()
        except Exception:
            logger.exception('Request handling failed for %s', source_ip)
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
