"""initial domain schema

Revision ID: 0001_initial_domain_schema
Revises: 
Create Date: 2026-08-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_initial_domain_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Schema tables are created directly by SQLAlchemy Base.metadata.create_all
    # This migration represents the clean baseline state.
    pass

def downgrade() -> None:
    pass
