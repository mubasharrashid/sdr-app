-- ============================================================================
-- TABLE 21: OUTREACH_ACTIVITY_LOGS
-- Comprehensive log of all outreach activities
-- ============================================================================

CREATE TABLE outreach_activity_logs (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    sequence_step_id UUID REFERENCES campaign_sequences(id) ON DELETE SET NULL,
    
    -- Activity type
    activity_type VARCHAR(50) NOT NULL,  -- email_sent, email_opened, email_clicked, email_replied, email_bounced,
                                         -- call_made, call_connected, voicemail_left, call_failed,
                                         -- linkedin_connect, linkedin_message, linkedin_reply,
                                         -- meeting_booked, meeting_completed, meeting_cancelled,
                                         -- lead_created, lead_updated, status_changed
    
    -- Channel
    channel VARCHAR(30),  -- email, phone, linkedin, sms, system
    
    -- Activity details
    description TEXT,
    
    -- Related entities (polymorphic reference)
    related_type VARCHAR(50),  -- call_task, email_reply, meeting, etc.
    related_id UUID,
    
    -- Email-specific
    email_subject VARCHAR(500),
    email_message_id VARCHAR(255),
    
    -- Call-specific
    call_duration_seconds INTEGER,
    call_outcome VARCHAR(50),
    
    -- Link tracking
    link_url TEXT,
    link_clicked_at TIMESTAMPTZ,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Source
    source VARCHAR(50),  -- ai_agent, user, automation, webhook, import
    source_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- IP/Device (for tracking)
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(30),
    
    -- Timestamp
    activity_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_outreach_activity_tenant ON outreach_activity_logs(tenant_id);
CREATE INDEX idx_outreach_activity_lead ON outreach_activity_logs(lead_id);
CREATE INDEX idx_outreach_activity_campaign ON outreach_activity_logs(campaign_id);
CREATE INDEX idx_outreach_activity_type ON outreach_activity_logs(activity_type);
CREATE INDEX idx_outreach_activity_channel ON outreach_activity_logs(channel);
CREATE INDEX idx_outreach_activity_at ON outreach_activity_logs(activity_at DESC);
CREATE INDEX idx_outreach_activity_lead_type ON outreach_activity_logs(lead_id, activity_type);

-- Composite for timeline queries
CREATE INDEX idx_outreach_activity_lead_timeline ON outreach_activity_logs(lead_id, activity_at DESC);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE outreach_activity_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY outreach_activity_logs_tenant_isolation ON outreach_activity_logs
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY outreach_activity_logs_service_role ON outreach_activity_logs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE outreach_activity_logs IS 'Comprehensive log of all outreach activities';
COMMENT ON COLUMN outreach_activity_logs.activity_type IS 'Activity type: email_sent, email_opened, call_made, meeting_booked, etc.';
COMMENT ON COLUMN outreach_activity_logs.source IS 'Activity source: ai_agent, user, automation, webhook, import';
