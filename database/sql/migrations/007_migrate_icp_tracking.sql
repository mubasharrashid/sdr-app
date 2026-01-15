-- ============================================================================
-- Migration: ICP Tracking Table
-- ============================================================================
-- Adds multi-tenancy support and optional ICP table reference
-- ============================================================================

-- Add tenant_id column
ALTER TABLE icp_tracking 
ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;

-- Add reference to icps table (optional - for backward compatibility with Excel ICPs)
ALTER TABLE icp_tracking 
ADD COLUMN IF NOT EXISTS icp_table_id UUID REFERENCES icps(id) ON DELETE SET NULL;

-- Add additional tracking fields
ALTER TABLE icp_tracking
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'failed'));

ALTER TABLE icp_tracking
ADD COLUMN IF NOT EXISTS error_message TEXT;

ALTER TABLE icp_tracking
ADD COLUMN IF NOT EXISTS last_error_at TIMESTAMPTZ;

-- Pagination improvements
ALTER TABLE icp_tracking
ADD COLUMN IF NOT EXISTS total_pages INTEGER;

ALTER TABLE icp_tracking
ADD COLUMN IF NOT EXISTS leads_per_page INTEGER DEFAULT 100;

-- Rate limiting
ALTER TABLE icp_tracking
ADD COLUMN IF NOT EXISTS daily_leads_fetched INTEGER DEFAULT 0;

ALTER TABLE icp_tracking
ADD COLUMN IF NOT EXISTS last_daily_reset_at TIMESTAMPTZ;

-- Provider info
ALTER TABLE icp_tracking
ADD COLUMN IF NOT EXISTS data_provider VARCHAR(50) DEFAULT 'apollo';

ALTER TABLE icp_tracking
ADD COLUMN IF NOT EXISTS provider_search_id VARCHAR(255);  -- External search/job ID

-- Metadata
ALTER TABLE icp_tracking
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

-- Indexes
CREATE INDEX IF NOT EXISTS idx_icp_tracking_tenant ON icp_tracking(tenant_id);
CREATE INDEX IF NOT EXISTS idx_icp_tracking_icp_table ON icp_tracking(icp_table_id);
CREATE INDEX IF NOT EXISTS idx_icp_tracking_status ON icp_tracking(status);
CREATE INDEX IF NOT EXISTS idx_icp_tracking_icp_id ON icp_tracking(icp_id);

-- Drop old index if exists
DROP INDEX IF EXISTS idx_icp_tracking_icp_code;

-- Row Level Security
ALTER TABLE icp_tracking ENABLE ROW LEVEL SECURITY;

-- Drop existing policies
DROP POLICY IF EXISTS icp_tracking_tenant_isolation ON icp_tracking;
DROP POLICY IF EXISTS icp_tracking_service_role_full_access ON icp_tracking;

-- Create new policies
CREATE POLICY icp_tracking_tenant_isolation ON icp_tracking
    FOR ALL
    USING (
        tenant_id IS NULL OR 
        tenant_id = current_setting('app.current_tenant_id', true)::uuid
    )
    WITH CHECK (
        tenant_id IS NULL OR 
        tenant_id = current_setting('app.current_tenant_id', true)::uuid
    );

CREATE POLICY icp_tracking_service_role_full_access ON icp_tracking
    FOR ALL
    USING (current_setting('role', true) = 'service_role')
    WITH CHECK (current_setting('role', true) = 'service_role');

-- Comments
COMMENT ON TABLE icp_tracking IS 'Tracks lead fetching progress for ICP-based lead generation';
COMMENT ON COLUMN icp_tracking.tenant_id IS 'Tenant that owns this tracking record';
COMMENT ON COLUMN icp_tracking.icp_table_id IS 'Optional reference to ICP definition in icps table';
COMMENT ON COLUMN icp_tracking.icp_id IS 'Legacy ICP identifier (for Excel-defined ICPs)';
COMMENT ON COLUMN icp_tracking.current_page IS 'Current pagination page for data provider API';
COMMENT ON COLUMN icp_tracking.daily_leads_fetched IS 'Leads fetched today (reset daily)';
