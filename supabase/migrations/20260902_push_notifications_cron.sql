-- ============================================================================
-- FastUI Sales: Production Web Push & Reminder Scheduler Setup
-- ============================================================================
-- Run this SQL in your Supabase SQL Editor (Dashboard > SQL Editor)
--
-- This script:
-- 1. Creates a high-performance partial index for pending unnotified reminders
-- 2. Creates the atomic `claim_due_reminders` stored procedure with FOR UPDATE SKIP LOCKED
-- 3. Enables `pg_cron` and `pg_net` extensions for scheduled Edge Function invocation
-- 4. Schedules the cron job to run every minute
-- ============================================================================

-- 1. High-Performance Partial Index for Due Reminders
-- Only indexes rows that are 'pending' and have not yet been notified.
-- Keeps the index tiny and queries instantaneous even with millions of historical records.
CREATE INDEX IF NOT EXISTS idx_reminders_due_unnotified 
ON reminders (due_at) 
WHERE status = 'pending' AND notification_sent_at IS NULL;

-- 2. Atomic Stored Procedure: claim_due_reminders
-- Atomically selects due reminders, claims them by setting notification_sent_at = NOW(),
-- and returns them with their associated business_name in a single round trip.
-- 'FOR UPDATE SKIP LOCKED' guarantees that concurrent runs never double-deliver.
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
        WHERE r.status = 'pending'
          AND r.due_at <= NOW()
          AND r.notification_sent_at IS NULL
        ORDER BY r.due_at ASC
        LIMIT batch_limit
        FOR UPDATE SKIP LOCKED
    ),
    claimed AS (
        UPDATE reminders r
        SET notification_sent_at = NOW(),
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
-- 3. Supabase Cron (pg_cron + pg_net) Setup
-- ============================================================================
-- Enable pg_cron and pg_net extensions if not already enabled
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;

-- NOTE: Replace the placeholders below with your actual values:
-- [YOUR-PROJECT-REF]: Your Supabase project reference (e.g., abcdefghijklm)
-- [YOUR-SERVICE-ROLE-KEY]: Your Supabase Service Role Key (from Dashboard > Settings > API)
--
-- Un-comment and execute the block below once your project reference and keys are set:

/*
SELECT cron.schedule(
    'process-due-reminders-job',
    '* * * * *', -- Run every minute
    $$
    SELECT net.http_post(
        url := 'https://[YOUR-PROJECT-REF].supabase.co/functions/v1/process-reminders',
        headers := jsonb_build_object(
            'Content-Type', 'application/json',
            'Authorization', 'Bearer [YOUR-SERVICE-ROLE-KEY]'
        ),
        body := '{}'::jsonb
    ) AS request_id;
    $$
);
*/

-- To verify or manage scheduled jobs:
-- SELECT * FROM cron.job;
-- SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 20;
-- To unschedule if needed:
-- SELECT cron.unschedule('process-due-reminders-job');
