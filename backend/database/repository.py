# All queries (create, filter, paginate, aggregate), and event helpers.

import json
import logging
from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import (
    AuditLogModel,
    SecurityEventModel,
    SourceObservationModel,
    UserModel,
)

logger = logging.getLogger(__name__)

class UserRepository:

    @staticmethod
    async def get_by_email(
        session: AsyncSession,
        email: str,
    ) -> UserModel | None:

        result = await session.execute(
            select(UserModel).where(
                UserModel.email == email
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def count_users(session: AsyncSession) -> int:

        result = await session.execute(
            select(func.count(UserModel.id)
            )
        )

        return result.scalar_one()

    @staticmethod
    async def create(
        session: AsyncSession,
        username: str,
        email:str,
        password_hash: str,
    ) -> UserModel:

        user = UserModel(
            username=username,
            email=email,
            password_hash=password_hash,
            role='administrator',
        )
        print(user,"hello brooooooooooooooooooooo")
        session.add(user)
        await session.flush()

        return user
    
    
    
#from now on these class are for honeypot engine 
class EventRepository:
    """
    All database operations for security events.

    Each method receives a session from the FastAPI dependency injector.
    The session is committed/rolled-back by the get_db() context manager.
    """

    @staticmethod
    async def create(session: AsyncSession, event_data: dict) -> SecurityEventModel:
        """Insert a new security event row."""
        row = SecurityEventModel(
            event_id=event_data['event_id'],
            source_ip=event_data['source_ip'],
            timestamp=event_data['timestamp'],
            attack_category=event_data['attack_category'],
            severity=event_data['severity'],
            confidence=event_data.get('confidence', 0.0),
            detector_names=json.dumps(event_data.get('detector_names', [])),
            detection_reasons=json.dumps(event_data.get('detection_reasons', [])),
            evidence=json.dumps(event_data.get('evidence', {})),
            target=event_data.get('target', '/'),
            method=event_data.get('method', 'GET'),
            path=event_data.get('path', '/'),
            request_id=event_data.get('request_id', ''),
            metadata_json=json.dumps(event_data.get('metadata', {})),
        )
        session.add(row)
        await session.flush()  # Assign the auto-increment ID.
        return row

    @staticmethod
    async def get_by_event_id(session: AsyncSession, event_id: str) -> SecurityEventModel | None:
        """Fetch a single event by its UUID."""
        result = await session.execute(
            select(SecurityEventModel)
            .options(selectinload(SecurityEventModel.annotations))
            .where(SecurityEventModel.event_id == event_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_events(
        session: AsyncSession,
        page: int = 1,
        page_size: int = 50,
        source_ip: str = None,
        severity: str = None,
        attack_category: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        search: str = None,
        sort_by: str = 'timestamp',
        sort_dir: str = 'desc',
    ) -> tuple:
        """
        Return (list_of_events, total_count) with optional filters.

        Filters are ANDed together.
        """
        query = select(SecurityEventModel)

        # Apply filters.
        if source_ip:
            query = query.where(SecurityEventModel.source_ip == source_ip)
        if severity:
            query = query.where(SecurityEventModel.severity == severity)
        if attack_category:
            query = query.where(SecurityEventModel.attack_category == attack_category)
        if start_time:
            query = query.where(SecurityEventModel.timestamp >= start_time)
        if end_time:
            query = query.where(SecurityEventModel.timestamp <= end_time)
        if search:
            # Simple text search across path, source_ip, and detection_reasons.
            like = f'%{search}%'
            query = query.where(
                SecurityEventModel.path.like(like) |
                SecurityEventModel.source_ip.like(like) |
                SecurityEventModel.detection_reasons.like(like)
            )

        # Count total matching rows.
        count_q = select(func.count()).select_from(query.subquery())
        total = (await session.execute(count_q)).scalar_one()

        sort_map = {
            'timestamp': SecurityEventModel.timestamp,
            'severity': SecurityEventModel.severity,
            'source_ip': SecurityEventModel.source_ip,
            'attack_category': SecurityEventModel.attack_category,
            'path': SecurityEventModel.path,
        }
        sort_col = sort_map.get(sort_by, SecurityEventModel.timestamp)
        query = query.order_by(sort_col.asc() if sort_dir == 'asc' else desc(sort_col))
        query = query.offset((page - 1) * page_size).limit(page_size)

        rows = (await session.execute(query)).scalars().all()
        return rows, total

    @staticmethod
    async def count_total(session: AsyncSession) -> int:
        result = await session.execute(select(func.count(SecurityEventModel.id)))
        return result.scalar_one()

    @staticmethod
    async def count_by_severity(session: AsyncSession) -> dict:
        """Return {severity: count} dictionary."""
        result = await session.execute(
            select(SecurityEventModel.severity, func.count(SecurityEventModel.id))
            .group_by(SecurityEventModel.severity)
        )
        return {row[0]: row[1] for row in result.fetchall()}

    @staticmethod
    async def count_by_category(session: AsyncSession) -> dict:
        """Return {category: count} dictionary."""
        result = await session.execute(
            select(SecurityEventModel.attack_category, func.count(SecurityEventModel.id))
            .group_by(SecurityEventModel.attack_category)
        )
        return {row[0]: row[1] for row in result.fetchall()}

    @staticmethod
    async def count_last_24h(session: AsyncSession) -> int:
        from datetime import timedelta
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        result = await session.execute(
            select(func.count(SecurityEventModel.id))
            .where(SecurityEventModel.timestamp >= cutoff)
        )
        return result.scalar_one()

    @staticmethod
    async def top_targets(session: AsyncSession, limit: int = 10) -> list:
        """Return [(path, count)] for the most targeted endpoints."""
        result = await session.execute(
            select(SecurityEventModel.path, func.count(SecurityEventModel.id).label('cnt'))
            .group_by(SecurityEventModel.path)
            .order_by(desc('cnt'))
            .limit(limit)
        )
        return result.fetchall()

    @staticmethod
    async def timeline(
        session: AsyncSession,
        hours: int = 24,
        bucket_minutes: int = 60,
        source_ip: str | None = None,
    ) -> list:
        """Return hourly event counts for the timeline chart."""
        from datetime import timedelta
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        query = select(SecurityEventModel.timestamp).where(
            SecurityEventModel.timestamp >= cutoff
        )
        if source_ip:
            query = query.where(SecurityEventModel.source_ip == source_ip)
        result = await session.execute(query.order_by(SecurityEventModel.timestamp))
        timestamps = [row[0] for row in result.fetchall()]

        # Bucket into hourly intervals.
        buckets = {}
        for ts in timestamps:
            # Round down to the nearest hour.
            bucket_key = ts.replace(minute=0, second=0, microsecond=0)
            bucket_str = bucket_key.isoformat()
            buckets[bucket_str] = buckets.get(bucket_str, 0) + 1

        return [
            {'time': k, 'count': v}
            for k, v in sorted(buckets.items())
        ]

    @staticmethod
    async def related_events(
        session: AsyncSession,
        source_ip: str,
        exclude_id: str,
        limit: int = 10,
    ) -> list:
        result = await session.execute(
            select(SecurityEventModel)
            .where(
                SecurityEventModel.source_ip == source_ip,
                SecurityEventModel.event_id != exclude_id,
            )
            .order_by(desc(SecurityEventModel.timestamp))
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def top_sources(session: AsyncSession, limit: int = 10) -> list:
        result = await session.execute(
            select(
                SecurityEventModel.source_ip,
                func.count(SecurityEventModel.id).label('cnt'),
            )
            .group_by(SecurityEventModel.source_ip)
            .order_by(desc('cnt'))
            .limit(limit)
        )
        return result.fetchall()

    @staticmethod
    async def hourly_activity(session: AsyncSession, hours: int = 24) -> list:
        from datetime import timedelta
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        result = await session.execute(
            select(SecurityEventModel.timestamp)
            .where(SecurityEventModel.timestamp >= cutoff)
        )
        hours_map = {i: 0 for i in range(24)}
        for (ts,) in result.fetchall():
            if ts is not None:
                hours_map[ts.hour] = hours_map.get(ts.hour, 0) + 1
        return [{'hour': h, 'count': hours_map[h]} for h in range(24)]


class SourceRepository:
    """Database operations for source observations (per-IP aggregates)."""

    @staticmethod
    async def upsert(session: AsyncSession, source_ip: str, event_data: dict):
        """Create or update the aggregated stats for a source IP."""
        result = await session.execute(
            select(SourceObservationModel).where(
                SourceObservationModel.source_ip == source_ip
            )
        )
        obs = result.scalar_one_or_none()
        now = datetime.now(UTC)

        if obs is None:
            # First event from this IP.
            obs = SourceObservationModel(
                source_ip=source_ip,
                first_seen=now,
                last_seen=now,
                total_events=1,
                last_category=event_data.get('attack_category'),
                category_counts=json.dumps({event_data.get('attack_category', 'unknown'): 1}),
                severity_counts=json.dumps({event_data.get('severity', 'low'): 1}),
            )
            session.add(obs)
        else:
            # Update existing record.
            obs.last_seen = now
            obs.total_events += 1
            obs.last_category = event_data.get('attack_category')

            # Update category counts.
            cats = json.loads(obs.category_counts)
            cat = event_data.get('attack_category', 'unknown')
            cats[cat] = cats.get(cat, 0) + 1
            obs.category_counts = json.dumps(cats)

            # Update severity counts.
            sevs = json.loads(obs.severity_counts)
            sev = event_data.get('severity', 'low')
            sevs[sev] = sevs.get(sev, 0) + 1
            obs.severity_counts = json.dumps(sevs)

    @staticmethod
    async def list_sources(session: AsyncSession, page: int = 1, page_size: int = 50) -> tuple:
        query = select(SourceObservationModel).order_by(desc(SourceObservationModel.last_seen))
        count_q = select(func.count()).select_from(query.subquery())
        total = (await session.execute(count_q)).scalar_one()
        query = query.offset((page - 1) * page_size).limit(page_size)
        rows = (await session.execute(query)).scalars().all()
        return rows, total

    @staticmethod
    async def get_by_ip(session: AsyncSession, ip: str) -> SourceObservationModel | None:
        result = await session.execute(
            select(SourceObservationModel).where(SourceObservationModel.source_ip == ip)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def count_unique_ips(session: AsyncSession) -> int:
        result = await session.execute(select(func.count(SourceObservationModel.id)))
        return result.scalar_one()

    @staticmethod
    async def write_audit(
        session: AsyncSession,
        actor: str,
        action: str,
        detail: str | None = None,
        source_ip: str | None = None,
    ) -> None:
        session.add(AuditLogModel(
            actor=actor,
            action=action,
            detail=detail,
            source_ip=source_ip,
        ))
