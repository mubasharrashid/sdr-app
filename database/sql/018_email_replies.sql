-- ============================================================================
-- TABLE 18: EMAIL_REPLIES
-- Email reply tracking and analysis
-- ============================================================================

CREATE TABLE email_replies (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    sequence_step_id UUID REFERENCES campaign_sequences(id) ON DELETE SET NULL,
    
    -- Email details
    message_id VARCHAR(255),
    thread_id VARCHAR(255),
    
    -- From/To
    from_email VARCHAR(255) NOT NULL,
    from_name VARCHAR(255),
    to_email VARCHAR(255) NOT NULL,
    
    -- Content
    subject VARCHAR(500),
    body_text TEXT,
    body_html TEXT,
    
    -- Attachments
    has_attachments BOOLEAN DEFAULT FALSE,
    attachment_count INTEGER DEFAULT 0,
    attachments JSONB DEFAULT '[]',
    
    -- Classification
    reply_type VARCHAR(30),  -- interested, not_interested, out_of_office, unsubscribe, question, meeting_request, other
    is_auto_reply BOOLEAN DEFAULT FALSE,
    is_out_of_office BOOLEAN DEFAULT FALSE,
    is_bounce BOOLEAN DEFAULT FALSE,
    
    -- AI analysis
    sentiment VARCHAR(20),  -- positive, neutral, negative
    intent VARCHAR(50),  -- interested, objection, question, unsubscribe, spam
    confidence_score NUMERIC(3, 2),
    
    -- AI-generated response
    suggested_response TEXT,
    response_sent BOOLEAN DEFAULT FALSE,
    response_sent_at TIMESTAMPTZ,
    
    -- Action required
    requires_action BOOLEAN DEFAULT TRUE,
    action_taken VARCHAR(100),
    action_taken_at TIMESTAMPTZ,
    action_taken_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Integration data
    gmail_message_id VARCHAR(255),
    outlook_message_id VARCHAR(255),
    
    -- Timestamps
    received_at TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_email_replies_tenant ON email_replies(tenant_id);
CREATE INDEX idx_email_replies_lead ON email_replies(lead_id);
CREATE INDEX idx_email_replies_campaign ON email_replies(campaign_id);
CREATE INDEX idx_email_replies_type ON email_replies(reply_type);
CREATE INDEX idx_email_replies_received ON email_replies(received_at DESC);
CREATE INDEX idx_email_replies_thread ON email_replies(thread_id);
CREATE INDEX idx_email_replies_requires_action ON email_replies(requires_action) WHERE requires_action = true;

-- ============================================================================
-- TRIGGER
-- ============================================================================

CREATE TRIGGER trigger_email_replies_updated_at
    BEFORE UPDATE ON email_replies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE email_replies ENABLE ROW LEVEL SECURITY;

CREATE POLICY email_replies_tenant_isolation ON email_replies
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY email_replies_service_role ON email_replies
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE email_replies IS 'Email reply tracking and analysis';
COMMENT ON COLUMN email_replies.reply_type IS 'Reply type: interested, not_interested, out_of_office, unsubscribe, question, meeting_request, other';
COMMENT ON COLUMN email_replies.intent IS 'AI-detected intent: interested, objection, question, unsubscribe, spam';
