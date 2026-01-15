-- ============================================================================
-- TABLE 15: CAMPAIGN_SEQUENCES
-- Multi-step campaign sequences (email sequences, follow-ups, etc.)
-- ============================================================================

CREATE TABLE campaign_sequences (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Sequence order
    step_number INTEGER NOT NULL,
    
    -- Step identification
    name VARCHAR(255),
    description TEXT,
    
    -- Step type
    step_type VARCHAR(50) NOT NULL,  -- email, call, linkedin_message, linkedin_connect, wait, condition
    
    -- Timing
    delay_days INTEGER DEFAULT 0,
    delay_hours INTEGER DEFAULT 0,
    delay_minutes INTEGER DEFAULT 0,
    
    -- Condition for this step (when to execute)
    condition_type VARCHAR(50),  -- none, if_no_reply, if_opened, if_clicked, if_replied
    condition_value JSONB,
    
    -- Email content (for email steps)
    email_subject VARCHAR(500),
    email_body TEXT,
    email_template_id UUID,  -- Reference to a template if using one
    
    -- Call script (for call steps)
    call_script TEXT,
    call_objective VARCHAR(255),
    
    -- LinkedIn content (for LinkedIn steps)
    linkedin_message TEXT,
    linkedin_connection_note VARCHAR(300),  -- LinkedIn has 300 char limit
    
    -- AI settings for this step
    use_ai_generation BOOLEAN DEFAULT TRUE,
    ai_prompt_template TEXT,
    ai_variables JSONB DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metrics for this step
    total_sent INTEGER DEFAULT 0,
    total_opened INTEGER DEFAULT 0,
    total_clicked INTEGER DEFAULT 0,
    total_replied INTEGER DEFAULT 0,
    total_converted INTEGER DEFAULT 0,
    
    -- A/B testing
    is_ab_test BOOLEAN DEFAULT FALSE,
    ab_variant VARCHAR(10),  -- A, B, C, etc.
    ab_test_group_id UUID,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT campaign_sequences_step_unique UNIQUE (campaign_id, step_number)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_campaign_sequences_campaign ON campaign_sequences(campaign_id);
CREATE INDEX idx_campaign_sequences_tenant ON campaign_sequences(tenant_id);
CREATE INDEX idx_campaign_sequences_step ON campaign_sequences(campaign_id, step_number);
CREATE INDEX idx_campaign_sequences_type ON campaign_sequences(step_type);

-- ============================================================================
-- TRIGGER
-- ============================================================================

CREATE TRIGGER trigger_campaign_sequences_updated_at
    BEFORE UPDATE ON campaign_sequences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE campaign_sequences ENABLE ROW LEVEL SECURITY;

CREATE POLICY campaign_sequences_tenant_isolation ON campaign_sequences
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY campaign_sequences_service_role ON campaign_sequences
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE campaign_sequences IS 'Multi-step campaign sequences';
COMMENT ON COLUMN campaign_sequences.step_type IS 'Type: email, call, linkedin_message, linkedin_connect, wait, condition';
COMMENT ON COLUMN campaign_sequences.condition_type IS 'When to execute: none, if_no_reply, if_opened, if_clicked, if_replied';
