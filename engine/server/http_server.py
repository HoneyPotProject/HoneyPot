# The decoy HTTP listener, built on asyncio.start_server, with request size
# limits and timeouts.

from __future__ import annotations

import asyncio
import logging

from engine.server.request_handler import RequestHandler

logger = logging.getLogger(__name__)


class HoneypotHTTPServer:
    def __init__(
        self,
        handler: RequestHandler,
        host: str = '0.0.0.0',
        port: int = 8080,
    ) -> None:
        self._handler = handler
        self._host = host
        self._port = port
        self._server = None

    @property
    def running(self) -> bool:
        return self._server is not None

    @property
    def port(self) -> int:
        return self._port

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handler.handle,
            host=self._host,
            port=self._port,
        )
        logger.info('Decoy HTTP listener started on %s:%d', self._host, self._port)

    async def stop(self) -> None:
        if self._server is None:
            return
        self._server.close()
        await self._server.wait_closed()
        self._server = None
        logger.info('Decoy HTTP listener stopped')
