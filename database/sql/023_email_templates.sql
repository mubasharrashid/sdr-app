-- ============================================================================
-- TABLE 23: EMAIL_TEMPLATES
-- Email templates for outreach campaigns, organized by ICP person and sequence
-- ============================================================================

CREATE TABLE email_templates (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    icp_person_id UUID REFERENCES icps(id) ON DELETE SET NULL,
    
    -- Template identification
    template_name VARCHAR(255),
    icp_person_name VARCHAR(255),  -- Name of the ICP person/target for this template
    
    -- Email content
    subject VARCHAR(500) NOT NULL,
    body_content TEXT NOT NULL,
    
    -- Sequence information
    email_sequence INTEGER DEFAULT 1,  -- Step number in the email sequence (1, 2, 3, etc.)
    
    -- Template metadata
    template_type VARCHAR(50) DEFAULT 'outreach',  -- outreach, follow_up, reply, nurture, etc.
    description TEXT,
    
    -- Personalization variables
    variables JSONB DEFAULT '{}',  -- Available variables like {{first_name}}, {{company_name}}, etc.
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Usage tracking
    times_used INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    
    -- Creator tracking
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT email_templates_sequence_check CHECK (email_sequence >= 1)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_email_templates_tenant ON email_templates(tenant_id);
CREATE INDEX idx_email_templates_icp_person ON email_templates(icp_person_id);
CREATE INDEX idx_email_templates_sequence ON email_templates(tenant_id, icp_person_id, email_sequence);
CREATE INDEX idx_email_templates_type ON email_templates(template_type);
CREATE INDEX idx_email_templates_active ON email_templates(tenant_id, is_active) WHERE is_active = TRUE;
CREATE INDEX idx_email_templates_created_by ON email_templates(created_by);

-- ============================================================================
-- TRIGGER
-- ============================================================================

CREATE TRIGGER trigger_email_templates_updated_at
    BEFORE UPDATE ON email_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE email_templates ENABLE ROW LEVEL SECURITY;

CREATE POLICY email_templates_tenant_isolation ON email_templates
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY email_templates_service_role ON email_templates
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE email_templates IS 'Email templates for outreach campaigns, organized by ICP person and sequence step';
COMMENT ON COLUMN email_templates.icp_person_id IS 'Reference to ICP (Ideal Customer Profile) this template targets';
COMMENT ON COLUMN email_templates.icp_person_name IS 'Name of the ICP person/target persona for this template';
COMMENT ON COLUMN email_templates.email_sequence IS 'Step number in the email sequence (1 = first email, 2 = follow-up, etc.)';
COMMENT ON COLUMN email_templates.template_type IS 'Type: outreach, follow_up, reply, nurture, objection_handling, etc.';
COMMENT ON COLUMN email_templates.variables IS 'JSON object defining available personalization variables';
COMMENT ON COLUMN email_templates.times_used IS 'Counter tracking how many times this template has been used';
