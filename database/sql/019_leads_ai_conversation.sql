-- ============================================================================
-- TABLE 19: LEADS_AI_CONVERSATION
-- AI conversation history with leads
-- ============================================================================

CREATE TABLE leads_ai_conversation (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    execution_id UUID REFERENCES agent_executions(id) ON DELETE SET NULL,
    
    -- Conversation context
    channel VARCHAR(30) NOT NULL,  -- email, call, linkedin, sms, chat
    
    -- Message details
    role VARCHAR(20) NOT NULL,  -- system, assistant, user, function
    message_type VARCHAR(30),  -- greeting, question, response, objection_handling, closing, etc.
    
    -- Content
    content TEXT NOT NULL,
    
    -- For email/linkedin
    subject VARCHAR(500),
    
    -- For calls
    audio_url TEXT,
    duration_seconds INTEGER,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- AI model info
    model_used VARCHAR(100),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    
    -- Sentiment at this point
    sentiment VARCHAR(20),
    
    -- Related entities
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    call_task_id UUID REFERENCES call_tasks(id) ON DELETE SET NULL,
    email_reply_id UUID REFERENCES email_replies(id) ON DELETE SET NULL,
    
    -- Was this sent/delivered?
    is_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_leads_ai_conversation_tenant ON leads_ai_conversation(tenant_id);
CREATE INDEX idx_leads_ai_conversation_lead ON leads_ai_conversation(lead_id);
CREATE INDEX idx_leads_ai_conversation_agent ON leads_ai_conversation(agent_id);
CREATE INDEX idx_leads_ai_conversation_channel ON leads_ai_conversation(channel);
CREATE INDEX idx_leads_ai_conversation_created ON leads_ai_conversation(created_at DESC);
CREATE INDEX idx_leads_ai_conversation_lead_created ON leads_ai_conversation(lead_id, created_at);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE leads_ai_conversation ENABLE ROW LEVEL SECURITY;

CREATE POLICY leads_ai_conversation_tenant_isolation ON leads_ai_conversation
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY leads_ai_conversation_service_role ON leads_ai_conversation
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE leads_ai_conversation IS 'AI conversation history with leads';
COMMENT ON COLUMN leads_ai_conversation.role IS 'Message role: system, assistant, user, function';
COMMENT ON COLUMN leads_ai_conversation.channel IS 'Communication channel: email, call, linkedin, sms, chat';
