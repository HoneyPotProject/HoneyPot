# Engine settings: body size limit, time windows, thresholds, redaction list.
# Using one place means you won't scatter magic numbers through the detectors.

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EngineConfig:
    """Central numeric and redaction settings for the detection engine."""

    max_body_bytes: int = 8192
    max_request_bytes: int = 65536
    request_timeout_seconds: float = 10.0
    brute_force_window_seconds: int = 60
    brute_force_threshold: int = 5
    endpoint_enum_window_seconds: int = 60
    endpoint_enum_path_threshold: int = 12
    port_scan_window_seconds: int = 30
    port_scan_port_threshold: int = 4
    session_gap_seconds: int = 300
    max_header_bytes: int = 4096
    decoy_ports: tuple[int, ...] = (21, 22, 23, 3306, 3389, 6379)
    login_paths: tuple[str, ...] = (
        '/login',
        '/wp-login.php',
        '/admin/login',
        '/signin',
        '/user/login',
    )
    redacted_headers: tuple[str, ...] = (
        'authorization',
        'cookie',
        'proxy-authorization',
        'x-api-key',
        'x-auth-token',
    )
    redacted_fields: tuple[str, ...] = (
        'password',
        'passwd',
        'pass',
        'token',
        'secret',
        'api_key',
        'apikey',
        'authorization',
    )


DEFAULT_CONFIG = EngineConfig()
