# asyncio listeners on several decoy TCP ports. It logs each connection
# (IP, port, time) without serving real content.

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from engine.core.config import DEFAULT_CONFIG, EngineConfig
from engine.core.context import RequestContext
from engine.events.event_processor import EventProcessor
from engine.network.port_scan_detector import PortScanDetector

logger = logging.getLogger(__name__)


class ConnectionMonitor:
    def __init__(
        self,
        processor: EventProcessor,
        detector: PortScanDetector | None = None,
        config: EngineConfig | None = None,
        host: str = '0.0.0.0',
    ) -> None:
        self._processor = processor
        self._detector = detector or PortScanDetector()
        self._config = config or DEFAULT_CONFIG
        self._host = host
        self._servers: list[asyncio.AbstractServer] = []
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    @property
    def detector(self) -> PortScanDetector:
        return self._detector

    async def start(self) -> None:
        for port in self._config.decoy_ports:
            try:
                server = await asyncio.start_server(
                    lambda r, w, p=port: self._on_connection(r, w, p),
                    host=self._host,
                    port=port,
                )
                self._servers.append(server)
                logger.info('Decoy TCP listener on %s:%d', self._host, port)
            except OSError as exc:
                logger.warning('Could not bind decoy port %d: %s', port, exc)
        self._running = True

    async def stop(self) -> None:
        for server in self._servers:
            server.close()
            await server.wait_closed()
        self._servers.clear()
        self._running = False

    async def _on_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        port: int,
    ) -> None:
        peer = writer.get_extra_info('peername') or ('0.0.0.0', 0)
        source_ip = peer[0]
        try:
            result = self._detector.record(source_ip, port)
            if result:
                ctx = RequestContext(
                    source_ip=source_ip,
                    method='TCP',
                    path=f'port {port}',
                    query_params={},
                    headers={},
                    body=b'',
                    timestamp=datetime.now(timezone.utc),
                    request_id=str(uuid.uuid4()),
                    source_port=int(peer[1]) if len(peer) > 1 else 0,
                )
                await self._processor.process(ctx, [result])
            writer.write(b'')
            await writer.drain()
        except Exception:
            logger.debug('Decoy connection closed on port %s', port, exc_info=True)
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
