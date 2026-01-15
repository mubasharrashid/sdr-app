-- ============================================================================
-- TABLE 14: CAMPAIGNS
-- Marketing and outreach campaigns
-- ============================================================================

CREATE TABLE campaigns (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    
    -- Campaign identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Type and channel
    campaign_type VARCHAR(50) NOT NULL,  -- email, call, linkedin, multi-channel
    channel VARCHAR(50),  -- primary channel: email, phone, linkedin, sms
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft',  -- draft, scheduled, active, paused, completed, archived
    
    -- Scheduling
    scheduled_start_at TIMESTAMPTZ,
    scheduled_end_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Timezone for scheduling
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Sending schedule (when to send)
    sending_days TEXT[] DEFAULT ARRAY['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
    sending_start_time TIME DEFAULT '09:00',
    sending_end_time TIME DEFAULT '17:00',
    
    -- Rate limiting
    daily_limit INTEGER DEFAULT 100,
    hourly_limit INTEGER DEFAULT 20,
    
    -- Target audience
    target_criteria JSONB DEFAULT '{}',  -- Filters for lead selection
    
    -- Metrics
    total_leads INTEGER DEFAULT 0,
    leads_contacted INTEGER DEFAULT 0,
    leads_responded INTEGER DEFAULT 0,
    leads_converted INTEGER DEFAULT 0,
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,
    emails_replied INTEGER DEFAULT 0,
    emails_bounced INTEGER DEFAULT 0,
    calls_made INTEGER DEFAULT 0,
    calls_connected INTEGER DEFAULT 0,
    meetings_booked INTEGER DEFAULT 0,
    
    -- Settings
    settings JSONB DEFAULT '{}',
    
    -- AI settings
    use_ai_personalization BOOLEAN DEFAULT TRUE,
    ai_tone VARCHAR(50) DEFAULT 'professional',  -- professional, friendly, casual, formal
    
    -- Ownership
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_campaigns_tenant ON campaigns(tenant_id);
CREATE INDEX idx_campaigns_agent ON campaigns(agent_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_type ON campaigns(campaign_type);
CREATE INDEX idx_campaigns_created ON campaigns(created_at DESC);
CREATE INDEX idx_campaigns_scheduled ON campaigns(scheduled_start_at);

-- ============================================================================
-- TRIGGER
-- ============================================================================

CREATE TRIGGER trigger_campaigns_updated_at
    BEFORE UPDATE ON campaigns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;

CREATE POLICY campaigns_tenant_isolation ON campaigns
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY campaigns_service_role ON campaigns
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE campaigns IS 'Marketing and outreach campaigns';
COMMENT ON COLUMN campaigns.campaign_type IS 'Type: email, call, linkedin, multi-channel';
COMMENT ON COLUMN campaigns.target_criteria IS 'JSON filters for lead selection';
