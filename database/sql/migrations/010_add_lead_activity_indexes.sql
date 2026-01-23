-- ============================================================================
-- MIGRATION: Add indexes for lead activity fields
-- ============================================================================
-- Purpose: Optimize queries filtering by calls_made, emails_sent, 
--          emails_replied, meetings_booked for dashboard filtering
-- ============================================================================

-- Indexes for activity-based filtering
CREATE INDEX IF NOT EXISTS idx_leads_calls_made ON leads(tenant_id, calls_made) WHERE calls_made > 0;
CREATE INDEX IF NOT EXISTS idx_leads_emails_sent ON leads(tenant_id, emails_sent) WHERE emails_sent > 0;
CREATE INDEX IF NOT EXISTS idx_leads_emails_replied ON leads(tenant_id, emails_replied) WHERE emails_replied > 0;
CREATE INDEX IF NOT EXISTS idx_leads_meetings_booked ON leads(tenant_id, meetings_booked) WHERE meetings_booked > 0;

-- Composite index for "contacted" filter (calls OR emails)
-- This supports queries filtering by either calls_made > 0 OR emails_sent > 0
CREATE INDEX IF NOT EXISTS idx_leads_contacted ON leads(tenant_id) 
    WHERE calls_made > 0 OR emails_sent > 0;

-- Comments
COMMENT ON INDEX idx_leads_calls_made IS 'Optimizes filtering leads with calls made';
COMMENT ON INDEX idx_leads_emails_sent IS 'Optimizes filtering leads with emails sent';
COMMENT ON INDEX idx_leads_emails_replied IS 'Optimizes filtering leads with email replies';
COMMENT ON INDEX idx_leads_meetings_booked IS 'Optimizes filtering leads with meetings booked';
COMMENT ON INDEX idx_leads_contacted IS 'Optimizes filtering contacted leads (calls OR emails)';
