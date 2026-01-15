-- ============================================================================
-- MIGRATION: Modify existing email_replies table for multi-tenant support
-- ============================================================================

-- Add tenant_id column (required for multi-tenancy)
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;

-- Add campaign relationship
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL;
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS sequence_step_id UUID REFERENCES campaign_sequences(id) ON DELETE SET NULL;

-- Add message tracking
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS message_id VARCHAR(255);

-- Add sender info
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS from_name VARCHAR(255);
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS to_email VARCHAR(255);

-- Add body_html if only body_text exists
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS body_html TEXT;

-- Add attachments
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS has_attachments BOOLEAN DEFAULT FALSE;
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS attachment_count INTEGER DEFAULT 0;
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS attachments JSONB DEFAULT '[]';

-- Add classification
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS reply_type VARCHAR(30);
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS is_auto_reply BOOLEAN DEFAULT FALSE;
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS is_out_of_office BOOLEAN DEFAULT FALSE;
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS is_bounce BOOLEAN DEFAULT FALSE;

-- Add AI analysis
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS sentiment VARCHAR(20);
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS intent VARCHAR(50);
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS confidence_score NUMERIC(3, 2);

-- Add AI response
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS suggested_response TEXT;
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS response_sent BOOLEAN DEFAULT FALSE;
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS response_sent_at TIMESTAMPTZ;

-- Add action tracking
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS requires_action BOOLEAN DEFAULT TRUE;
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS action_taken VARCHAR(100);
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS action_taken_at TIMESTAMPTZ;
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS action_taken_by UUID REFERENCES users(id) ON DELETE SET NULL;

-- Add integration IDs
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS gmail_message_id VARCHAR(255);
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS outlook_message_id VARCHAR(255);

-- Add processed_at
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ;

-- Add updated_at if missing
ALTER TABLE email_replies ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_email_replies_tenant ON email_replies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_email_replies_lead ON email_replies(lead_id);
CREATE INDEX IF NOT EXISTS idx_email_replies_campaign ON email_replies(campaign_id);
CREATE INDEX IF NOT EXISTS idx_email_replies_type ON email_replies(reply_type);
CREATE INDEX IF NOT EXISTS idx_email_replies_received ON email_replies(received_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_replies_thread ON email_replies(thread_id);
CREATE INDEX IF NOT EXISTS idx_email_replies_requires_action ON email_replies(requires_action) WHERE requires_action = true;

-- ============================================================================
-- TRIGGER
-- ============================================================================

DROP TRIGGER IF EXISTS trigger_email_replies_updated_at ON email_replies;
CREATE TRIGGER trigger_email_replies_updated_at
    BEFORE UPDATE ON email_replies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE email_replies ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS email_replies_tenant_isolation ON email_replies;
CREATE POLICY email_replies_tenant_isolation ON email_replies
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

DROP POLICY IF EXISTS email_replies_service_role ON email_replies;
CREATE POLICY email_replies_service_role ON email_replies
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
