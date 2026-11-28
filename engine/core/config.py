"""Central engine settings. Detectors read from here; they never hardcode limits."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EngineConfig:
    # Request limits (used later by the listener/collector)
    max_body_bytes: int = 16_384
    max_header_bytes: int = 8_192
    max_header_count: int = 64
    max_url_length: int = 2_048
    request_timeout_seconds: float = 10.0
    max_connections: int = 100

    # Normalizer
    max_decode_rounds: int = 3

    # Bounded memory for stateful detectors
    max_tracked_sources: int = 10_000
    max_entries_per_source: int = 200

    # Endpoint enumeration (starting values from the guide)
    endpoint_enum_distinct_paths: int = 15
    endpoint_enum_window_seconds: int = 60
    endpoint_enum_error_count: int = 10
    endpoint_enum_error_window_seconds: int = 30

    # Brute force
    brute_force_attempts: int = 5
    brute_force_window_seconds: int = 60

    # Port scan
    port_scan_distinct_ports: int = 5
    port_scan_window_seconds: int = 30

    # Sessions
    session_idle_gap_seconds: int = 1_800

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if isinstance(value, (int, float)) and value <= 0:
                raise ValueError(f"{name} must be greater than 0")
