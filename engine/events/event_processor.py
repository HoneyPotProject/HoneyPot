# Merges detector results and analyzer output into one normalized SecurityEvent,
# generates the UUID, picks the final category and severity, and passes the
# event to the sink. This is the only place where classification happens.

from __future__ import annotations

import logging
import uuid
from typing import Any

from engine.analyzers.automation import AutomationAnalyzer
from engine.analyzers.behavior import BehaviorAnalyzer
from engine.analyzers.session_analyzer import SessionAnalyzer
from engine.core.context import RequestContext
from engine.core.detection import (
    SEVERITY_ORDER,
    AttackCategory,
    DetectionResult,
    Severity,
)
from engine.events.event import SecurityEvent
from engine.events.storage_interface import EventSink

logger = logging.getLogger(__name__)


class EventProcessor:
    """Classify detector output and hand a SecurityEvent to the EventSink."""

    def __init__(
        self,
        sink: EventSink,
        behavior: BehaviorAnalyzer | None = None,
        automation: AutomationAnalyzer | None = None,
        sessions: SessionAnalyzer | None = None,
    ) -> None:
        self._sink = sink
        self._behavior = behavior or BehaviorAnalyzer()
        self._automation = automation or AutomationAnalyzer()
        self._sessions = sessions or SessionAnalyzer()

    async def process(
        self,
        ctx: RequestContext,
        results: list[DetectionResult],
    ) -> SecurityEvent | None:
        if not results:
            return None

        dominant = self._pick_dominant(results)
        confidence = sum(r.confidence for r in results) / len(results)
        reasons = [r.reason for r in results]
        evidence: dict[str, Any] = {}
        for result in results:
            if result.evidence:
                evidence[result.detector_name] = result.evidence

        behavior = self._behavior.score(ctx.source_ip, dominant.category)
        automation = self._automation.likelihood(
            ctx.source_ip,
            ctx.timestamp,
            ctx.headers.get('user-agent', ''),
        )
        session = self._sessions.process(
            ctx.source_ip,
            ctx.timestamp,
            ctx.headers.get('cookie', ''),
        )

        event = SecurityEvent(
            event_id=uuid.uuid4(),
            source_ip=ctx.source_ip,
            timestamp=ctx.timestamp,
            attack_category=dominant.category,
            severity=dominant.severity,
            confidence=round(min(1.0, max(0.0, confidence)), 4),
            detection_reasons=reasons,
            evidence=evidence,
            target=ctx.path or '/',
            method=ctx.method,
            path=ctx.path or '/',
            request_id=ctx.request_id,
            detector_names=[r.detector_name for r in results],
            related_results=list(results),
            metadata={
                'behavioral_score': behavior,
                'automation_likelihood': automation,
                'session': session,
                'source_port': ctx.source_port,
                'malformed': ctx.malformed,
            },
        )

        try:
            await self._sink.save(event)
        except Exception:
            logger.exception(
                'EventSink.save failed for event_id=%s; engine continues',
                event.event_id,
            )
        return event

    @staticmethod
    def _pick_dominant(results: list[DetectionResult]) -> DetectionResult:
        def key(result: DetectionResult) -> tuple[int, float]:
            try:
                rank = SEVERITY_ORDER.index(result.severity)
            except ValueError:
                rank = 0
            return (rank, result.confidence)

        return max(results, key=key)
