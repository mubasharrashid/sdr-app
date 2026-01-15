-- ============================================================================
-- Table 22: ICPs (Ideal Customer Profiles)
-- ============================================================================
-- Defines targeting criteria for lead generation and outreach
-- ============================================================================

CREATE TABLE IF NOT EXISTS icps (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Tenant (multi-tenancy)
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- ICP Identification
    icp_code VARCHAR(50) NOT NULL,  -- e.g., "ICP-UAE-PWR-UTIL-01"
    name VARCHAR(255) NOT NULL,      -- e.g., "UAE Power Generation - Government Utilities"
    description TEXT,
    
    -- Reference Person (who defined/owns this ICP)
    reference_person VARCHAR(255),
    
    -- Targeting Criteria - Company
    target_industries TEXT[],        -- e.g., ['power generation', 'utilities', 'energy']
    target_company_sizes TEXT[],     -- e.g., ['51-200', '201-500', '501-1000']
    min_employees INTEGER,
    max_employees INTEGER,
    target_revenue_range VARCHAR(100),  -- e.g., "$10M-$50M"
    
    -- Targeting Criteria - Geography
    target_countries TEXT[],         -- e.g., ['United Arab Emirates', 'Saudi Arabia']
    target_regions TEXT[],           -- e.g., ['Middle East', 'GCC']
    target_cities TEXT[],
    
    -- Targeting Criteria - Personas
    target_titles TEXT[],            -- e.g., ['CEO', 'CTO', 'VP Engineering']
    target_seniorities TEXT[],       -- e.g., ['c_suite', 'vp', 'director', 'manager']
    target_departments TEXT[],       -- e.g., ['engineering', 'operations', 'procurement']
    
    -- Targeting Criteria - Technographics
    target_technologies TEXT[],      -- e.g., ['Salesforce', 'HubSpot']
    exclude_technologies TEXT[],
    
    -- Targeting Criteria - Keywords
    include_keywords TEXT[],
    exclude_keywords TEXT[],
    
    -- Data Provider Settings (Apollo, etc.)
    data_provider VARCHAR(50) DEFAULT 'apollo',  -- apollo, zoominfo, linkedin, etc.
    provider_search_params JSONB DEFAULT '{}',   -- Raw API search parameters
    
    -- Lead Scoring Weights
    scoring_weights JSONB DEFAULT '{}',  -- e.g., {"title_match": 20, "industry_match": 15}
    min_lead_score INTEGER DEFAULT 0,
    
    -- Campaign Association
    default_campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    
    -- Limits & Quotas
    max_leads_to_fetch INTEGER,          -- Total limit
    daily_fetch_limit INTEGER,           -- Per day limit
    leads_fetched_total INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('draft', 'active', 'paused', 'completed', 'archived')),
    priority INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),  -- 1 = highest
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT unique_tenant_icp_code UNIQUE (tenant_id, icp_code)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_icps_tenant ON icps(tenant_id);
CREATE INDEX IF NOT EXISTS idx_icps_status ON icps(status);
CREATE INDEX IF NOT EXISTS idx_icps_code ON icps(icp_code);
CREATE INDEX IF NOT EXISTS idx_icps_priority ON icps(priority) WHERE status = 'active';

-- Row Level Security
ALTER TABLE icps ENABLE ROW LEVEL SECURITY;

-- Policies
DROP POLICY IF EXISTS icps_tenant_isolation ON icps;
CREATE POLICY icps_tenant_isolation ON icps
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

DROP POLICY IF EXISTS icps_service_role_full_access ON icps;
CREATE POLICY icps_service_role_full_access ON icps
    FOR ALL
    USING (current_setting('role', true) = 'service_role')
    WITH CHECK (current_setting('role', true) = 'service_role');

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_icps_updated_at ON icps;
CREATE TRIGGER update_icps_updated_at
    BEFORE UPDATE ON icps
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE icps IS 'Ideal Customer Profile definitions for targeted lead generation';
COMMENT ON COLUMN icps.icp_code IS 'Unique code identifier for the ICP';
COMMENT ON COLUMN icps.provider_search_params IS 'Raw search parameters for data provider API';
COMMENT ON COLUMN icps.scoring_weights IS 'Weights for calculating lead scores based on ICP match';
