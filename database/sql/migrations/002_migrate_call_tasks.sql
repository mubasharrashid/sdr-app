-- ============================================================================
-- MIGRATION: Modify existing call_tasks table for multi-tenant support
-- ============================================================================

-- Add tenant_id column (required for multi-tenancy)
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;

-- Add relationships
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL;
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS agent_id UUID REFERENCES agents(id) ON DELETE SET NULL;

-- Add call details
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50);
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS caller_id VARCHAR(50);

-- Add scheduling
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMPTZ;
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC';

-- Add status
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'pending';

-- Add call context
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS call_objective VARCHAR(255);
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS call_script TEXT;
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS talking_points JSONB DEFAULT '[]';

-- Add AI context
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS lead_context JSONB DEFAULT '{}';
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS ai_instructions TEXT;

-- Add Retell AI specific fields
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS retell_call_id VARCHAR(255);
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS retell_agent_id VARCHAR(255);

-- Add call timing
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS call_started_at TIMESTAMPTZ;
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS call_ended_at TIMESTAMPTZ;
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS call_duration_seconds INTEGER;

-- Add recording
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS recording_url TEXT;
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS recording_duration_seconds INTEGER;

-- Add transcription
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS transcript TEXT;
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS transcript_summary TEXT;

-- Add AI analysis
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS sentiment VARCHAR(20);
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS key_topics TEXT[];
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS action_items JSONB DEFAULT '[]';
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS next_steps TEXT;

-- Add outcome
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS outcome VARCHAR(50);
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS meeting_booked BOOLEAN DEFAULT FALSE;
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS callback_scheduled_at TIMESTAMPTZ;

-- Add quality
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS quality_score INTEGER;
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS quality_notes TEXT;

-- Add cost tracking
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS cost_cents INTEGER DEFAULT 0;

-- Add timestamps
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE call_tasks ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id) ON DELETE SET NULL;

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_call_tasks_tenant ON call_tasks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_call_tasks_lead ON call_tasks(lead_id);
CREATE INDEX IF NOT EXISTS idx_call_tasks_campaign ON call_tasks(campaign_id);
CREATE INDEX IF NOT EXISTS idx_call_tasks_status ON call_tasks(status);
CREATE INDEX IF NOT EXISTS idx_call_tasks_scheduled ON call_tasks(scheduled_at) WHERE status = 'scheduled';
CREATE INDEX IF NOT EXISTS idx_call_tasks_retell ON call_tasks(retell_call_id);

-- ============================================================================
-- TRIGGER
-- ============================================================================

DROP TRIGGER IF EXISTS trigger_call_tasks_updated_at ON call_tasks;
CREATE TRIGGER trigger_call_tasks_updated_at
    BEFORE UPDATE ON call_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE call_tasks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS call_tasks_tenant_isolation ON call_tasks;
CREATE POLICY call_tasks_tenant_isolation ON call_tasks
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

DROP POLICY IF EXISTS call_tasks_service_role ON call_tasks;
CREATE POLICY call_tasks_service_role ON call_tasks
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
