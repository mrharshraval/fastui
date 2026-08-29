"""Initial FastUI Unified Domain Schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Users Table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), server_default='sales', nullable=False),
        sa.Column('verification_otp', sa.String(length=32), nullable=True),
        sa.Column('verification_otp_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)

    # 2. Businesses Table
    op.create_table(
        'businesses',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('business_name', sa.String(length=255), nullable=False),
        sa.Column('raw_business_name', sa.String(length=500), nullable=True),
        sa.Column('normalized_business_name', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=255), nullable=True),
        sa.Column('normalized_phone', sa.String(length=64), nullable=True),
        sa.Column('normalized_website', sa.String(length=255), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('postal_code', sa.String(length=32), nullable=True),
        sa.Column('phone', sa.String(length=64), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('has_whatsapp', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('website_status', sa.String(length=50), server_default='unknown', nullable=False),
        sa.Column('source_platform', sa.String(length=100), server_default='discover', nullable=True),
        sa.Column('qualification_status', sa.String(length=50), server_default='unqualified', nullable=False),
        sa.Column('last_outreach_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_contacted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_businesses_id'), 'businesses', ['id'], unique=False)
    op.create_index(op.f('ix_businesses_business_name'), 'businesses', ['business_name'], unique=False)
    op.create_index(op.f('ix_businesses_normalized_business_name'), 'businesses', ['normalized_business_name'], unique=False)
    op.create_index(op.f('ix_businesses_category'), 'businesses', ['category'], unique=False)
    op.create_index(op.f('ix_businesses_city'), 'businesses', ['city'], unique=False)
    op.create_index(op.f('ix_businesses_normalized_phone'), 'businesses', ['normalized_phone'], unique=False)
    op.create_index(op.f('ix_businesses_normalized_website'), 'businesses', ['normalized_website'], unique=False)
    op.create_index(op.f('ix_businesses_qualification_status'), 'businesses', ['qualification_status'], unique=False)
    op.create_index(op.f('ix_businesses_created_at'), 'businesses', ['created_at'], unique=False)

    # 3. Leads Table
    op.create_table(
        'leads',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('assigned_to', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('stage', sa.String(length=50), server_default='lead', nullable=False),
        sa.Column('priority', sa.String(length=50), server_default='medium', nullable=False),
        sa.Column('signal', sa.String(length=50), server_default='warm', nullable=False),
        sa.Column('score', sa.Integer(), server_default='50', nullable=False),
        sa.Column('source', sa.String(length=100), server_default='discover', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_leads_id'), 'leads', ['id'], unique=False)
    op.create_index(op.f('ix_leads_business_id'), 'leads', ['business_id'], unique=True)
    op.create_index(op.f('ix_leads_assigned_to'), 'leads', ['assigned_to'], unique=False)
    op.create_index(op.f('ix_leads_stage'), 'leads', ['stage'], unique=False)
    op.create_index(op.f('ix_leads_priority'), 'leads', ['priority'], unique=False)
    op.create_index(op.f('ix_leads_score'), 'leads', ['score'], unique=False)
    op.create_index(op.f('ix_leads_created_at'), 'leads', ['created_at'], unique=False)

    # 4. Contacts Table
    op.create_table(
        'contacts',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('job_title', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=64), nullable=True),
        sa.Column('normalized_phone', sa.String(length=64), nullable=True),
        sa.Column('is_decision_maker', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_contacts_id'), 'contacts', ['id'], unique=False)
    op.create_index(op.f('ix_contacts_business_id'), 'contacts', ['business_id'], unique=False)
    op.create_index(op.f('ix_contacts_email'), 'contacts', ['email'], unique=False)
    op.create_index(op.f('ix_contacts_phone'), 'contacts', ['phone'], unique=False)

    # 5. Notes Table
    op.create_table(
        'notes',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contact_id', sa.Integer(), sa.ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_notes_id'), 'notes', ['id'], unique=False)
    op.create_index(op.f('ix_notes_business_id'), 'notes', ['business_id'], unique=False)

    # 6. Tasks Table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contact_id', sa.Integer(), sa.ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)
    op.create_index(op.f('ix_tasks_business_id'), 'tasks', ['business_id'], unique=False)
    op.create_index(op.f('ix_tasks_status'), 'tasks', ['status'], unique=False)
    op.create_index(op.f('ix_tasks_due_date'), 'tasks', ['due_date'], unique=False)

    # 7. Reminders Table
    op.create_table(
        'reminders',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contact_id', sa.Integer(), sa.ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_reminders_id'), 'reminders', ['id'], unique=False)
    op.create_index(op.f('ix_reminders_business_id'), 'reminders', ['business_id'], unique=False)
    op.create_index(op.f('ix_reminders_status'), 'reminders', ['status'], unique=False)
    op.create_index(op.f('ix_reminders_due_at'), 'reminders', ['due_at'], unique=False)

    # 8. Outreaches Table
    op.create_table(
        'outreaches',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contact_id', sa.Integer(), sa.ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('channel', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('attempted_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_outreaches_id'), 'outreaches', ['id'], unique=False)
    op.create_index(op.f('ix_outreaches_business_id'), 'outreaches', ['business_id'], unique=False)
    op.create_index(op.f('ix_outreaches_attempted_at'), 'outreaches', ['attempted_at'], unique=False)

    # 9. Interactions Table
    op.create_table(
        'interactions',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contact_id', sa.Integer(), sa.ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('outreach_id', sa.Integer(), sa.ForeignKey('outreaches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('summary', sa.String(length=500), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_interactions_id'), 'interactions', ['id'], unique=False)
    op.create_index(op.f('ix_interactions_business_id'), 'interactions', ['business_id'], unique=False)
    op.create_index(op.f('ix_interactions_occurred_at'), 'interactions', ['occurred_at'], unique=False)

    # 10. Activities Table
    op.create_table(
        'activities',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('business_id', sa.Integer(), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=True),
        sa.Column('contact_id', sa.Integer(), sa.ForeignKey('contacts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_activities_id'), 'activities', ['id'], unique=False)
    op.create_index(op.f('ix_activities_business_id'), 'activities', ['business_id'], unique=False)
    op.create_index(op.f('ix_activities_type'), 'activities', ['type'], unique=False)
    op.create_index(op.f('ix_activities_created_at'), 'activities', ['created_at'], unique=False)

    # 11. Discovery Jobs Table
    op.create_table(
        'discovery_jobs',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('target_audience', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('progress_percent', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_discovered', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_processed', sa.Integer(), server_default='0', nullable=False),
        sa.Column('new_leads', sa.Integer(), server_default='0', nullable=False),
        sa.Column('existing_businesses', sa.Integer(), server_default='0', nullable=False),
        sa.Column('duplicates', sa.Integer(), server_default='0', nullable=False),
        sa.Column('skipped', sa.Integer(), server_default='0', nullable=False),
        sa.Column('errors', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f('ix_discovery_jobs_id'), 'discovery_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_discovery_jobs_status'), 'discovery_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_discovery_jobs_created_at'), 'discovery_jobs', ['created_at'], unique=False)

    # 12. Export Jobs Table
    op.create_table(
        'export_jobs',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='pending', nullable=False),
        sa.Column('export_type', sa.String(length=50), nullable=False),
        sa.Column('file_format', sa.String(length=20), server_default='csv', nullable=False),
        sa.Column('total_records', sa.Integer(), server_default='0', nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('filters_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f('ix_export_jobs_id'), 'export_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_export_jobs_status'), 'export_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_export_jobs_created_at'), 'export_jobs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('export_jobs')
    op.drop_table('discovery_jobs')
    op.drop_table('activities')
    op.drop_table('interactions')
    op.drop_table('outreaches')
    op.drop_table('reminders')
    op.drop_table('tasks')
    op.drop_table('notes')
    op.drop_table('contacts')
    op.drop_table('leads')
    op.drop_table('businesses')
    op.drop_table('users')
