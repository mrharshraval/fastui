"""Add prospect_demos and demo_events tables

Revision ID: 0002_prospect_demos
Revises: 0001_initial_schema
Create Date: 2026-09-05

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_prospect_demos'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. prospect_demos table
    op.create_table(
        'prospect_demos',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='active', nullable=False),
        sa.Column('template_id', sa.String(length=64), server_default='dental-default', nullable=False),
        sa.Column('custom_overrides', sa.JSON(), nullable=True),
        sa.Column('view_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_prospect_demos_id'), 'prospect_demos', ['id'], unique=False)
    op.create_index(op.f('ix_prospect_demos_business_id'), 'prospect_demos', ['business_id'], unique=False)
    op.create_index(op.f('ix_prospect_demos_token'), 'prospect_demos', ['token'], unique=True)

    # 2. demo_events table
    op.create_table(
        'demo_events',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('demo_id', sa.Integer(), sa.ForeignKey('prospect_demos.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=True),
        sa.Column('page_path', sa.String(length=255), nullable=True),
        sa.Column('referrer', sa.String(length=255), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_demo_events_id'), 'demo_events', ['id'], unique=False)
    op.create_index(op.f('ix_demo_events_demo_id'), 'demo_events', ['demo_id'], unique=False)
    op.create_index(op.f('ix_demo_events_event_type'), 'demo_events', ['event_type'], unique=False)


def downgrade() -> None:
    op.drop_table('demo_events')
    op.drop_table('prospect_demos')
