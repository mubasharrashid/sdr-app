-- ============================================================================
-- MIGRATION: Modify existing outreach_activity_logs table for multi-tenant support
-- ============================================================================

-- Add tenant_id column (required for multi-tenancy)
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;

-- Add campaign relationship
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL;
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS sequence_step_id UUID REFERENCES campaign_sequences(id) ON DELETE SET NULL;

-- Rename action_type to activity_type if needed, or add activity_type
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS activity_type VARCHAR(50);
UPDATE outreach_activity_logs SET activity_type = action_type WHERE activity_type IS NULL AND action_type IS NOT NULL;

-- Add channel
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS channel VARCHAR(30);

-- Add description
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS description TEXT;

-- Add related entity tracking
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS related_type VARCHAR(50);
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS related_id UUID;

-- Add email message ID
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS email_message_id VARCHAR(255);

-- Add call-specific fields
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS call_duration_seconds INTEGER;
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS call_outcome VARCHAR(50);

-- Add link tracking
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS link_url TEXT;
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS link_clicked_at TIMESTAMPTZ;

-- Add source tracking
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS source VARCHAR(50);
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS source_user_id UUID REFERENCES users(id) ON DELETE SET NULL;

-- Add IP/Device tracking
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS ip_address INET;
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS user_agent TEXT;
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS device_type VARCHAR(30);

-- Rename performed_at to activity_at if needed
ALTER TABLE outreach_activity_logs ADD COLUMN IF NOT EXISTS activity_at TIMESTAMPTZ;
UPDATE outreach_activity_logs SET activity_at = performed_at WHERE activity_at IS NULL AND performed_at IS NOT NULL;
UPDATE outreach_activity_logs SET activity_at = created_at WHERE activity_at IS NULL;

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_outreach_activity_tenant ON outreach_activity_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_outreach_activity_lead ON outreach_activity_logs(lead_id);
CREATE INDEX IF NOT EXISTS idx_outreach_activity_campaign ON outreach_activity_logs(campaign_id);
CREATE INDEX IF NOT EXISTS idx_outreach_activity_type ON outreach_activity_logs(activity_type);
CREATE INDEX IF NOT EXISTS idx_outreach_activity_channel ON outreach_activity_logs(channel);
CREATE INDEX IF NOT EXISTS idx_outreach_activity_at ON outreach_activity_logs(activity_at DESC);
CREATE INDEX IF NOT EXISTS idx_outreach_activity_lead_type ON outreach_activity_logs(lead_id, activity_type);
CREATE INDEX IF NOT EXISTS idx_outreach_activity_lead_timeline ON outreach_activity_logs(lead_id, activity_at DESC);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE outreach_activity_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS outreach_activity_logs_tenant_isolation ON outreach_activity_logs;
CREATE POLICY outreach_activity_logs_tenant_isolation ON outreach_activity_logs
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

DROP POLICY IF EXISTS outreach_activity_logs_service_role ON outreach_activity_logs;
CREATE POLICY outreach_activity_logs_service_role ON outreach_activity_logs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
