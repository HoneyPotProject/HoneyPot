"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-11-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'security_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('source_ip', sa.String(length=45), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attack_category', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('detector_names', sa.Text(), nullable=False),
        sa.Column('detection_reasons', sa.Text(), nullable=False),
        sa.Column('evidence', sa.Text(), nullable=False),
        sa.Column('target', sa.String(length=500), nullable=False),
        sa.Column('method', sa.String(length=20), nullable=False),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('request_id', sa.String(length=36), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id'),
    )
    op.create_index('ix_security_events_event_id', 'security_events', ['event_id'])
    op.create_index('ix_security_events_source_ip', 'security_events', ['source_ip'])
    op.create_index('ix_security_events_timestamp', 'security_events', ['timestamp'])
    op.create_index('ix_security_events_attack_category', 'security_events', ['attack_category'])
    op.create_index('ix_security_events_severity', 'security_events', ['severity'])
    op.create_index('ix_events_ip_timestamp', 'security_events', ['source_ip', 'timestamp'])

    op.create_table(
        'source_observations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_ip', sa.String(length=45), nullable=False),
        sa.Column('first_seen', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_events', sa.Integer(), nullable=False),
        sa.Column('last_category', sa.String(length=50), nullable=True),
        sa.Column('category_counts', sa.Text(), nullable=False),
        sa.Column('severity_counts', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_ip'),
    )
    op.create_index('ix_source_observations_source_ip', 'source_observations', ['source_ip'])

    op.create_table(
        'analyst_annotations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('analyst_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['security_events.event_id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_analyst_annotations_event_id', 'analyst_annotations', ['event_id'])

    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actor', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('source_ip', sa.String(length=45), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_log_timestamp', 'audit_log', ['timestamp'])


def downgrade() -> None:
    op.drop_table('audit_log')
    op.drop_table('analyst_annotations')
    op.drop_table('source_observations')
    op.drop_table('security_events')
