# IP validation, private/public classification and normalization helpers.

from __future__ import annotations

import ipaddress


def normalize_ip(value: str) -> str:
    raw = (value or '').strip()
    if raw.startswith('::ffff:'):
        raw = raw[7:]
    if '%' in raw:
        raw = raw.split('%', 1)[0]
    try:
        return str(ipaddress.ip_address(raw))
    except ValueError:
        return raw or '0.0.0.0'


def is_valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(normalize_ip(value))
        return True
    except ValueError:
        return False


def is_private_ip(value: str) -> bool:
    try:
        addr = ipaddress.ip_address(normalize_ip(value))
        return addr.is_private or addr.is_loopback or addr.is_link_local
    except ValueError:
        return False
