-- ============================================================================
-- MIGRATION: Modify existing leads_ai_conversation table for multi-tenant support
-- ============================================================================

-- Add tenant_id column (required for multi-tenancy)
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;

-- Add relationships
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS agent_id UUID REFERENCES agents(id) ON DELETE SET NULL;
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS execution_id UUID REFERENCES agent_executions(id) ON DELETE SET NULL;
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL;
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS call_task_id UUID REFERENCES call_tasks(id) ON DELETE SET NULL;

-- Add channel (email, call, linkedin, sms, chat)
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS channel VARCHAR(30) DEFAULT 'email';

-- Add role (system, assistant, user, function)
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'assistant';

-- Add message_type (greeting, question, response, objection_handling, closing)
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS message_type VARCHAR(30);

-- Add content (consolidate messages)
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS content TEXT;
-- Populate from existing columns
UPDATE leads_ai_conversation 
SET content = COALESCE(message_from_agent_ai, '') || COALESCE(message_from_email, '')
WHERE content IS NULL;

-- Add subject for email/linkedin
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS subject VARCHAR(500);

-- Add audio fields for calls
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS audio_url TEXT;
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS duration_seconds INTEGER;

-- Add metadata
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';

-- Add AI model info
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS model_used VARCHAR(100);
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS prompt_tokens INTEGER;
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS completion_tokens INTEGER;

-- Rename confidence_score if it exists or add sentiment
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS sentiment VARCHAR(20);

-- Add is_sent tracking
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS is_sent BOOLEAN DEFAULT FALSE;
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ;

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_leads_ai_conversation_tenant ON leads_ai_conversation(tenant_id);
CREATE INDEX IF NOT EXISTS idx_leads_ai_conversation_lead ON leads_ai_conversation(lead_id);
CREATE INDEX IF NOT EXISTS idx_leads_ai_conversation_agent ON leads_ai_conversation(agent_id);
CREATE INDEX IF NOT EXISTS idx_leads_ai_conversation_channel ON leads_ai_conversation(channel);
CREATE INDEX IF NOT EXISTS idx_leads_ai_conversation_created ON leads_ai_conversation(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_ai_conversation_lead_created ON leads_ai_conversation(lead_id, created_at);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE leads_ai_conversation ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS leads_ai_conversation_tenant_isolation ON leads_ai_conversation;
CREATE POLICY leads_ai_conversation_tenant_isolation ON leads_ai_conversation
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

DROP POLICY IF EXISTS leads_ai_conversation_service_role ON leads_ai_conversation;
CREATE POLICY leads_ai_conversation_service_role ON leads_ai_conversation
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
