-- ============================================================================
-- MIGRATION: Modify existing leads table for multi-tenant support
-- ============================================================================

-- Add tenant_id column (required for multi-tenancy)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;

-- Add campaign relationship
ALTER TABLE leads ADD COLUMN IF NOT EXISTS campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS assigned_to UUID REFERENCES users(id) ON DELETE SET NULL;

-- Rename/map existing columns if needed
-- organization_name -> company_name
ALTER TABLE leads ADD COLUMN IF NOT EXISTS company_name VARCHAR(255);
UPDATE leads SET company_name = organization_name WHERE company_name IS NULL AND organization_name IS NOT NULL;

-- organization_primary_domain -> company_domain
ALTER TABLE leads ADD COLUMN IF NOT EXISTS company_domain VARCHAR(255);
UPDATE leads SET company_domain = organization_primary_domain WHERE company_domain IS NULL AND organization_primary_domain IS NOT NULL;

-- title -> job_title
ALTER TABLE leads ADD COLUMN IF NOT EXISTS job_title VARCHAR(255);
UPDATE leads SET job_title = title WHERE job_title IS NULL AND title IS NOT NULL;

-- Add missing contact fields
ALTER TABLE leads ADD COLUMN IF NOT EXISTS department VARCHAR(100);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS twitter_url TEXT;

-- Add lead status (rename outreach_status to status if needed)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'new';
UPDATE leads SET status = outreach_status WHERE status = 'new' AND outreach_status IS NOT NULL;

-- Add scoring fields
ALTER TABLE leads ADD COLUMN IF NOT EXISTS lead_score INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS engagement_score INTEGER DEFAULT 0;

-- Add sequence tracking (rename current_step to current_sequence_step)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS current_sequence_step INTEGER DEFAULT 0;
UPDATE leads SET current_sequence_step = current_step WHERE current_sequence_step = 0 AND current_step IS NOT NULL;

-- Add reply tracking
ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_replied_at TIMESTAMPTZ;
UPDATE leads SET last_replied_at = responded_at WHERE last_replied_at IS NULL AND responded_at IS NOT NULL;

ALTER TABLE leads ADD COLUMN IF NOT EXISTS next_followup_at TIMESTAMPTZ;
UPDATE leads SET next_followup_at = next_action_at WHERE next_followup_at IS NULL AND next_action_at IS NOT NULL;

-- Add email tracking fields
ALTER TABLE leads ADD COLUMN IF NOT EXISTS emails_replied INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS emails_bounced INTEGER DEFAULT 0;

-- Add call tracking
ALTER TABLE leads ADD COLUMN IF NOT EXISTS calls_made INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS calls_connected INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS voicemails_left INTEGER DEFAULT 0;

-- Add meeting tracking
ALTER TABLE leads ADD COLUMN IF NOT EXISTS meetings_booked INTEGER DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS meetings_completed INTEGER DEFAULT 0;

-- Add AI personalization context
ALTER TABLE leads ADD COLUMN IF NOT EXISTS personalization_context JSONB DEFAULT '{}';
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ai_notes TEXT;

-- Add custom fields and tags
ALTER TABLE leads ADD COLUMN IF NOT EXISTS custom_fields JSONB DEFAULT '{}';
ALTER TABLE leads ADD COLUMN IF NOT EXISTS tags TEXT[];

-- Add CRM sync fields
ALTER TABLE leads ADD COLUMN IF NOT EXISTS crm_id VARCHAR(255);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS crm_synced_at TIMESTAMPTZ;

-- Add opt-out fields
ALTER TABLE leads ADD COLUMN IF NOT EXISTS is_unsubscribed BOOLEAN DEFAULT FALSE;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS unsubscribed_at TIMESTAMPTZ;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS do_not_contact BOOLEAN DEFAULT FALSE;

-- Add timestamps if missing
ALTER TABLE leads ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE leads ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Rename enrichment fields
ALTER TABLE leads ADD COLUMN IF NOT EXISTS enrichment_data JSONB DEFAULT '{}';
UPDATE leads SET enrichment_data = raw_enrich::jsonb WHERE enrichment_data = '{}' AND raw_enrich IS NOT NULL;

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_leads_tenant ON leads(tenant_id);
CREATE INDEX IF NOT EXISTS idx_leads_campaign ON leads(campaign_id);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_leads_assigned ON leads(assigned_to);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(lead_score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_next_followup ON leads(next_followup_at) WHERE next_followup_at IS NOT NULL;

-- ============================================================================
-- TRIGGER (if not exists)
-- ============================================================================

DROP TRIGGER IF EXISTS trigger_leads_updated_at ON leads;
CREATE TRIGGER trigger_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS leads_tenant_isolation ON leads;
CREATE POLICY leads_tenant_isolation ON leads
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

DROP POLICY IF EXISTS leads_service_role ON leads;
CREATE POLICY leads_service_role ON leads
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- NOTE: After migration, you'll need to:
-- 1. Assign tenant_id to existing leads
-- 2. Verify data mappings are correct
-- ============================================================================
