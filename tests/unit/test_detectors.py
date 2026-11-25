from engine.collectors.request_collector import RequestCollector
from engine.core.config import EngineConfig
from engine.core.engine import DetectionEngine
from engine.detectors.command_injection import CommandInjectionDetector
from engine.detectors.directory_enum import DirectoryEnumerationDetector
from engine.detectors.path_traversal import PathTraversalDetector
from engine.detectors.sql_injection import SQLInjectionDetector
from engine.detectors.xss import XSSDetector


def _ctx(raw: bytes):
    return RequestCollector().collect(raw, '127.0.0.1', 4444)


def test_sql_injection_detects_union_select():
    ctx = _ctx(b"GET /x?q=1'+UNION+SELECT+1 HTTP/1.1\r\nHost: h\r\n\r\n")
    results = SQLInjectionDetector().analyze(ctx)
    assert results
    assert results[0].category.value == 'sql_injection'


def test_xss_detects_script_tag():
    ctx = _ctx(b'GET /x?q=%3Cscript%3Ealert(1)%3C/script%3E HTTP/1.1\r\nHost: h\r\n\r\n')
    assert XSSDetector().analyze(ctx)


def test_path_traversal():
    ctx = _ctx(b'GET /static/../../../etc/passwd HTTP/1.1\r\nHost: h\r\n\r\n')
    assert PathTraversalDetector().analyze(ctx)


def test_command_injection():
    ctx = _ctx(b'GET /run?cmd=%3Bid HTTP/1.1\r\nHost: h\r\n\r\n')
    assert CommandInjectionDetector().analyze(ctx)


def test_directory_enum_env():
    ctx = _ctx(b'GET /.env HTTP/1.1\r\nHost: h\r\n\r\n')
    assert DirectoryEnumerationDetector().analyze(ctx)


def test_engine_isolates_detector_crash():
    class Boom:
        name = 'Boom'
        enabled = True
        detection_count = 0

        def analyze(self, ctx):
            raise RuntimeError('boom')

    engine = DetectionEngine()
    engine.register(Boom())  # type: ignore[arg-type]
    engine.register(DirectoryEnumerationDetector())
    ctx = _ctx(b'GET /.env HTTP/1.1\r\nHost: h\r\n\r\n')
    results = engine.analyze(ctx)
    assert any(r.detector_name == 'DirectoryEnumerationDetector' for r in results)


def test_collector_redacts_authorization():
    ctx = RequestCollector(EngineConfig()).collect(
        b'GET / HTTP/1.1\r\nHost: h\r\nAuthorization: Bearer secret-token\r\n\r\n',
        '127.0.0.1',
    )
    assert ctx.headers['authorization'] == '[REDACTED]'
