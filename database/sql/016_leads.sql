-- ============================================================================
-- TABLE 16: LEADS
-- Lead/prospect records
-- ============================================================================

CREATE TABLE leads (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Contact information
    email VARCHAR(255),
    phone VARCHAR(50),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name VARCHAR(255),
    
    -- Company information
    company_name VARCHAR(255),
    company_domain VARCHAR(255),
    job_title VARCHAR(255),
    department VARCHAR(100),
    
    -- Location
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    timezone VARCHAR(50),
    
    -- Social profiles
    linkedin_url TEXT,
    twitter_url TEXT,
    
    -- Lead source
    source VARCHAR(100),  -- import, apollo, linkedin, website, referral, etc.
    source_id VARCHAR(255),  -- External ID from source
    
    -- Lead status
    status VARCHAR(50) DEFAULT 'new',  -- new, contacted, engaged, qualified, converted, unqualified, do_not_contact
    
    -- Lead scoring
    lead_score INTEGER DEFAULT 0,
    engagement_score INTEGER DEFAULT 0,
    
    -- Outreach status
    current_sequence_step INTEGER DEFAULT 0,
    last_contacted_at TIMESTAMPTZ,
    last_replied_at TIMESTAMPTZ,
    next_followup_at TIMESTAMPTZ,
    
    -- Email tracking
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,
    emails_replied INTEGER DEFAULT 0,
    emails_bounced INTEGER DEFAULT 0,
    
    -- Call tracking
    calls_made INTEGER DEFAULT 0,
    calls_connected INTEGER DEFAULT 0,
    voicemails_left INTEGER DEFAULT 0,
    
    -- Meeting tracking
    meetings_booked INTEGER DEFAULT 0,
    meetings_completed INTEGER DEFAULT 0,
    
    -- AI enrichment
    enrichment_data JSONB DEFAULT '{}',
    enriched_at TIMESTAMPTZ,
    
    -- AI personalization context
    personalization_context JSONB DEFAULT '{}',
    ai_notes TEXT,
    
    -- Custom fields
    custom_fields JSONB DEFAULT '{}',
    tags TEXT[],
    
    -- CRM sync
    crm_id VARCHAR(255),
    crm_synced_at TIMESTAMPTZ,
    
    -- Opt-out
    is_unsubscribed BOOLEAN DEFAULT FALSE,
    unsubscribed_at TIMESTAMPTZ,
    do_not_contact BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT leads_email_or_phone CHECK (email IS NOT NULL OR phone IS NOT NULL)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_leads_tenant ON leads(tenant_id);
CREATE INDEX idx_leads_email ON leads(tenant_id, email);
CREATE INDEX idx_leads_campaign ON leads(campaign_id);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_assigned ON leads(assigned_to);
CREATE INDEX idx_leads_company ON leads(tenant_id, company_domain);
CREATE INDEX idx_leads_score ON leads(lead_score DESC);
CREATE INDEX idx_leads_created ON leads(created_at DESC);
CREATE INDEX idx_leads_next_followup ON leads(next_followup_at) WHERE next_followup_at IS NOT NULL;
CREATE INDEX idx_leads_source ON leads(source);

-- ============================================================================
-- TRIGGER
-- ============================================================================

CREATE TRIGGER trigger_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

CREATE POLICY leads_tenant_isolation ON leads
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY leads_service_role ON leads
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE leads IS 'Lead/prospect records';
COMMENT ON COLUMN leads.status IS 'Lead status: new, contacted, engaged, qualified, converted, unqualified, do_not_contact';
COMMENT ON COLUMN leads.enrichment_data IS 'Data from enrichment services (Apollo, etc.)';
