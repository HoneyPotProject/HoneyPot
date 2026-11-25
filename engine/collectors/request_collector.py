# Turns raw HTTP data into a RequestContext. It validates the IP with
# ipaddress, parses the URL and query string, URL-decodes values, truncates
# the body to the size limit, and redacts Authorization, Cookie and password
# fields.

from __future__ import annotations

import ipaddress
from datetime import datetime, timezone
from types import MappingProxyType
from urllib.parse import parse_qs, unquote, unquote_plus, urlsplit
import uuid

from engine.core.config import DEFAULT_CONFIG, EngineConfig
from engine.core.context import RequestContext
from engine.network.ip_utils import normalize_ip


def multi_decode(value: str, rounds: int = 3) -> str:
    current = value
    for _ in range(rounds):
        decoded = unquote_plus(unquote(current))
        if decoded == current:
            break
        current = decoded
    return current


class RequestCollector:
    """Convert raw HTTP bytes into a redacted RequestContext."""

    def __init__(self, config: EngineConfig | None = None) -> None:
        self._config = config or DEFAULT_CONFIG

    def collect(self, raw: bytes, source_ip: str, source_port: int = 0) -> RequestContext:
        ip = normalize_ip(source_ip)
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            ip = '0.0.0.0'

        truncated = raw[: self._config.max_request_bytes]
        malformed = False
        try:
            text = truncated.decode('utf-8', errors='replace')
        except Exception:
            text = ''
            malformed = True

        head, sep, body_text = text.partition('\r\n\r\n')
        if not sep:
            head, sep, body_text = text.partition('\n\n')
        if not sep:
            malformed = True

        lines = head.splitlines()
        request_line = lines[0] if lines else ''
        parts = request_line.split()
        if len(parts) >= 2:
            method = parts[0].upper()[:16]
            raw_target = parts[1]
        else:
            method = 'UNKNOWN'
            raw_target = '/'
            malformed = True

        split = urlsplit(raw_target)
        path = multi_decode(split.path or '/')[:500]
        query_raw = parse_qs(split.query, keep_blank_values=True)
        query: dict[str, str] = {}
        for key, values in query_raw.items():
            decoded_key = multi_decode(key)[:100]
            decoded_val = multi_decode(values[0] if values else '')[:500]
            if decoded_key.lower() in self._config.redacted_fields:
                query[decoded_key] = '[REDACTED]'
            else:
                query[decoded_key] = decoded_val

        headers: dict[str, str] = {}
        for line in lines[1:]:
            if ':' not in line:
                continue
            name, _, value = line.partition(':')
            key = name.strip().lower()[:100]
            val = value.strip()[: self._config.max_header_bytes]
            if key in self._config.redacted_headers or key in self._config.redacted_fields:
                headers[key] = '[REDACTED]'
            else:
                headers[key] = val

        body_bytes = body_text.encode('utf-8', errors='replace')[: self._config.max_body_bytes]
        if any(field in body_text.lower() for field in ('password=', 'passwd=', 'token=')):
            body_bytes = b'[REDACTED FORM BODY]'

        return RequestContext(
            source_ip=ip,
            method=method,
            path=path or '/',
            query_params=MappingProxyType(query),
            headers=MappingProxyType(headers),
            body=body_bytes,
            timestamp=datetime.now(timezone.utc),
            request_id=str(uuid.uuid4()),
            source_port=source_port,
            raw_size=len(raw),
            malformed=malformed,
        )
