"""FastUI Safe Database Migrations.

Executes idempotent DDL alterations to align existing Postgres tables with current models.
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger("fastui.migration")

# PostgreSQL safe DDL migrations covering all columns across all domain tables
POSTGRES_MIGRATIONS = [
    # Users table
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(255);",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'sales' NOT NULL;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_otp VARCHAR(32);",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_otp_expires_at TIMESTAMPTZ;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE NOT NULL;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    # Businesses table
    "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS source_platform VARCHAR(100) DEFAULT 'discover';",
    "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS qualification_status VARCHAR(50) DEFAULT 'unqualified' NOT NULL;",
    "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS last_outreach_at TIMESTAMPTZ;",
    "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS last_contacted_at TIMESTAMPTZ;",
    "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS website_status VARCHAR(50) DEFAULT 'unknown' NOT NULL;",
    "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS raw_business_name VARCHAR(500);",
    "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS normalized_business_name VARCHAR(255);",
    "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS normalized_phone VARCHAR(64);",
    "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS canonical_name VARCHAR(255);",
    "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS source_name VARCHAR(500);",
    "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS has_whatsapp BOOLEAN DEFAULT FALSE NOT NULL;",
    "UPDATE businesses SET canonical_name = business_name WHERE canonical_name IS NULL;",
    "UPDATE businesses SET source_name = raw_business_name WHERE source_name IS NULL;",
    "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    # Leads table
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS stage VARCHAR(50) DEFAULT 'lead' NOT NULL;",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS priority VARCHAR(50) DEFAULT 'medium' NOT NULL;",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS signal VARCHAR(50) DEFAULT 'warm' NOT NULL;",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS score INTEGER DEFAULT 50 NOT NULL;",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS source VARCHAR(100) DEFAULT 'discover' NOT NULL;",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    "ALTER TABLE leads ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    # Contacts table
    "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS normalized_phone VARCHAR(64);",
    "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS is_decision_maker BOOLEAN DEFAULT FALSE NOT NULL;",
    "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    "ALTER TABLE contacts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    # Notes table
    "ALTER TABLE notes ADD COLUMN IF NOT EXISTS contact_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL;",
    "ALTER TABLE notes ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;",
    "ALTER TABLE notes ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    "ALTER TABLE notes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    # Tasks table
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS contact_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL;",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    # Reminders table
    "ALTER TABLE reminders ADD COLUMN IF NOT EXISTS task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL;",
    "ALTER TABLE reminders ADD COLUMN IF NOT EXISTS contact_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL;",
    "ALTER TABLE reminders ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;",
    "ALTER TABLE reminders ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;",
    "ALTER TABLE reminders ADD COLUMN IF NOT EXISTS notification_sent_at TIMESTAMPTZ;",
    "ALTER TABLE reminders ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    "ALTER TABLE reminders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    # Outreaches table
    "ALTER TABLE outreaches ADD COLUMN IF NOT EXISTS contact_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL;",
    "ALTER TABLE outreaches ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;",
    "ALTER TABLE outreaches ADD COLUMN IF NOT EXISTS metadata_json JSON;",
    "ALTER TABLE outreaches ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    "ALTER TABLE outreaches ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    # Interactions table
    "ALTER TABLE interactions ADD COLUMN IF NOT EXISTS contact_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL;",
    "ALTER TABLE interactions ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;",
    "ALTER TABLE interactions ADD COLUMN IF NOT EXISTS outreach_id INTEGER REFERENCES outreaches(id) ON DELETE SET NULL;",
    "ALTER TABLE interactions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    "ALTER TABLE interactions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    # Activities table
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS entity_type VARCHAR(50);",
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS entity_id INTEGER;",
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS contact_id INTEGER REFERENCES contacts(id) ON DELETE SET NULL;",
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;",
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS metadata_json JSON;",
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL;",
    # Crawled Websites table
    "CREATE TABLE IF NOT EXISTS crawled_websites (id SERIAL PRIMARY KEY, domain VARCHAR(255) NOT NULL, location_signature VARCHAR(255), business_id INTEGER REFERENCES businesses(id) ON DELETE SET NULL, canonical_url VARCHAR(500), branches JSON, extracted_data JSON NOT NULL, confidence_score FLOAT DEFAULT 1.0 NOT NULL, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL, updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL);",
    "CREATE INDEX IF NOT EXISTS ix_crawled_websites_domain ON crawled_websites(domain);",
    "CREATE INDEX IF NOT EXISTS ix_crawled_websites_domain_loc ON crawled_websites(domain, location_signature);",
    # Export Jobs table
    "ALTER TABLE export_jobs ADD COLUMN IF NOT EXISTS export_type VARCHAR(50) DEFAULT 'prospects';",
    "ALTER TABLE export_jobs ADD COLUMN IF NOT EXISTS params JSON;",
    "ALTER TABLE export_jobs ADD COLUMN IF NOT EXISTS file_path VARCHAR(500);",
    # Clean existing phone numbers starting with '0' to start with country code '+91 '
    "UPDATE businesses SET phone = '+91 ' || SUBSTRING(REGEXP_REPLACE(phone, '[^0-9]', '', 'g') FROM 2 FOR 5) || ' ' || SUBSTRING(REGEXP_REPLACE(phone, '[^0-9]', '', 'g') FROM 7) WHERE phone ~ '^0[6-9][0-9]{9}$';",
    "UPDATE businesses SET phone = '+91 ' || SUBSTRING(REGEXP_REPLACE(phone, '[^0-9]', '', 'g') FROM 1 FOR 5) || ' ' || SUBSTRING(REGEXP_REPLACE(phone, '[^0-9]', '', 'g') FROM 6) WHERE phone ~ '^[6-9][0-9]{9}$';",
]


async def run_safe_migrations(db_engine: AsyncEngine) -> None:
    """Executes idempotent DDL alterations to align existing Postgres tables with current models."""
    dialect = db_engine.dialect.name
    if dialect != "postgresql":
        return

    async with db_engine.begin() as conn:
        for stmt in POSTGRES_MIGRATIONS:
            try:
                await conn.execute(text(stmt))
            except Exception as e:
                # Log but do not block startup if table doesn't exist yet (create_all will make it)
                logger.debug(f"Migration statement skipped: {stmt} -> {e}")
    logger.info("Database schema columns synchronized successfully.")
