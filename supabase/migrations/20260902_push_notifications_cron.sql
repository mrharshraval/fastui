-- ============================================================================
-- FastUI Sales: Production Web Push & Reminder Scheduler Setup
-- ============================================================================
-- Run this migration in your Supabase SQL Editor (Dashboard > SQL Editor)
--
-- This script:
-- 1. Adds 'notification_processing_at' for safe distributed lease claiming
-- 2. Creates the atomic 'claim_due_reminders' stored procedure with lease locking
-- 3. Enables 'pg_cron', 'pg_net', and 'supabase_vault' extensions
-- 4. Idempotently configures the 1-minute cron job reading credentials from Vault
-- ============================================================================

-- 1. Lease Column & Partial Index for Due Reminders
-- Adds a temporary processing lease timestamp to prevent concurrent duplicate runs
-- without prematurely marking notification_sent_at.
ALTER TABLE reminders ADD COLUMN IF NOT EXISTS notification_processing_at timestamptz;

-- High-Performance Partial Index for Due Pending Reminders
CREATE INDEX IF NOT EXISTS idx_reminders_due_processing 
ON reminders (due_at) 
WHERE (status = 'PENDING' OR status = 'pending') AND notification_sent_at IS NULL;

-- 2. Atomic Stored Procedure: claim_due_reminders
-- Atomically selects due unnotified reminders, acquires a 5-minute processing lease
-- by setting notification_processing_at = NOW(), and returns them to the caller.
--
-- IMPORTANT: notification_sent_at is NOT touched here. It is only stamped by
-- the Edge Function once Web Push delivery actually succeeds.
-- 'FOR UPDATE SKIP LOCKED' guarantees that concurrent workers never collide.
CREATE OR REPLACE FUNCTION claim_due_reminders(batch_limit int DEFAULT 50)
RETURNS TABLE (
    id int,
    business_id int,
    user_id int,
    title text,
    notes text,
    due_at timestamptz,
    business_name text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN QUERY
    WITH due AS (
        SELECT r.id
        FROM reminders r
        WHERE (r.status::text = 'PENDING' OR r.status::text = 'pending')
          AND r.due_at <= NOW()
          AND r.notification_sent_at IS NULL
          AND (r.notification_processing_at IS NULL OR r.notification_processing_at < NOW() - INTERVAL '5 minutes')
        ORDER BY r.due_at ASC
        LIMIT batch_limit
        FOR UPDATE SKIP LOCKED
    ),
    claimed AS (
        UPDATE reminders r
        SET notification_processing_at = NOW(),
            updated_at = NOW()
        FROM due
        WHERE r.id = due.id
        RETURNING r.id, r.business_id, r.user_id, r.title, r.notes, r.due_at
    )
    SELECT 
        c.id, 
        c.business_id, 
        c.user_id, 
        c.title::text, 
        c.notes, 
        c.due_at,
        b.business_name::text
    FROM claimed c
    LEFT JOIN businesses b ON b.id = c.business_id;
END;
$$;

-- Grant execution to authenticated & service_role
GRANT EXECUTE ON FUNCTION claim_due_reminders(int) TO service_role;
GRANT EXECUTE ON FUNCTION claim_due_reminders(int) TO postgres;

-- ============================================================================
-- 3. Supabase Cron (pg_cron + pg_net + Supabase Vault) Setup
-- ============================================================================
-- Enable required extensions safely
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;
CREATE EXTENSION IF NOT EXISTS supabase_vault CASCADE;

-- Instructions to configure credentials in Supabase Vault:
-- Run the following commands ONCE in your Supabase SQL Editor or configure via Dashboard > Project Settings > Vault:
--
-- 1. Store your Supabase project URL (e.g. 'https://<your-project-ref>.supabase.co'):
--    SELECT vault.create_secret('https://<your-project-ref>.supabase.co', 'project_url');
--
-- 2. Store your Secret Key (from Dashboard > Project Settings > API > Secret keys):
--    SELECT vault.create_secret('<your-secret-key>', 'edge_function_secret');
--
-- To update existing secrets later:
--    SELECT vault.update_secret(<secret-id>, '<new-value>');

-- 4. Idempotent Cron Job Scheduling
-- Unschedule existing job if it exists to avoid duplicates
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'process-due-reminders-job') THEN
        PERFORM cron.unschedule('process-due-reminders-job');
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        NULL; -- Ignore if cron table or extension is not yet initialized
END $$;

-- Schedule the cron job to run every minute
-- Zero-Cost Optimized Scheduler:
-- 1. Checks if any pending reminders are actually due and not leased (0 HTTP overhead when idle).
-- 2. Dynamically fetches 'project_url' and 'edge_function_secret' from Supabase Vault (never hardcoded).
-- 3. Invokes Edge Function using 'apikey' header with the Secret Key.
SELECT cron.schedule(
    'process-due-reminders-job',
    '* * * * *', -- Evaluates every minute
    $$
    DO $do$
    DECLARE
        v_secret text;
        v_project_url text;
    BEGIN
        -- Fast zero-cost exit: only proceed if an unnotified reminder is due and not leased
        IF EXISTS (
            SELECT 1 FROM reminders 
            WHERE (status::text = 'PENDING' OR status::text = 'pending')
              AND due_at <= NOW() 
              AND notification_sent_at IS NULL
              AND (notification_processing_at IS NULL OR notification_processing_at < NOW() - INTERVAL '5 minutes')
        ) THEN
            -- Retrieve credentials dynamically from Supabase Vault
            SELECT decrypted_secret INTO v_secret 
            FROM vault.decrypted_secrets 
            WHERE name = 'edge_function_secret' 
            LIMIT 1;

            SELECT decrypted_secret INTO v_project_url 
            FROM vault.decrypted_secrets 
            WHERE name = 'project_url' 
            LIMIT 1;

            IF v_secret IS NOT NULL AND v_project_url IS NOT NULL THEN
                PERFORM net.http_post(
                    url := rtrim(v_project_url, '/') || '/functions/v1/reminders',
                    headers := jsonb_build_object(
                        'Content-Type', 'application/json',
                        'apikey', v_secret
                    ),
                    body := '{}'::jsonb
                );
            ELSE
                RAISE WARNING 'process-due-reminders-job: Missing edge_function_secret or project_url in vault.decrypted_secrets';
            END IF;
        END IF;
    END $do$;
    $$
);

-- To verify scheduled jobs:
-- SELECT * FROM cron.job;
-- SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 20;
