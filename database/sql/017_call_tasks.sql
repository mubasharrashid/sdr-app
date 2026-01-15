-- ============================================================================
-- TABLE 17: CALL_TASKS
-- AI call tasks for Retell AI integration
-- ============================================================================

CREATE TABLE call_tasks (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    
    -- Call details
    phone_number VARCHAR(50) NOT NULL,
    caller_id VARCHAR(50),
    
    -- Scheduling
    scheduled_at TIMESTAMPTZ,
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Status
    status VARCHAR(30) DEFAULT 'pending',  -- pending, scheduled, in_progress, completed, failed, cancelled, no_answer, voicemail
    
    -- Call context
    call_objective VARCHAR(255),
    call_script TEXT,
    talking_points JSONB DEFAULT '[]',
    
    -- AI context
    lead_context JSONB DEFAULT '{}',  -- Personalization data for AI
    ai_instructions TEXT,
    
    -- Retell AI specific
    retell_call_id VARCHAR(255),
    retell_agent_id VARCHAR(255),
    
    -- Call outcome
    call_started_at TIMESTAMPTZ,
    call_ended_at TIMESTAMPTZ,
    call_duration_seconds INTEGER,
    
    -- Recording
    recording_url TEXT,
    recording_duration_seconds INTEGER,
    
    -- Transcription
    transcript TEXT,
    transcript_summary TEXT,
    
    -- AI analysis
    sentiment VARCHAR(20),  -- positive, neutral, negative
    key_topics TEXT[],
    action_items JSONB DEFAULT '[]',
    next_steps TEXT,
    
    -- Outcome
    outcome VARCHAR(50),  -- interested, not_interested, callback, meeting_booked, voicemail, wrong_number, do_not_call
    meeting_booked BOOLEAN DEFAULT FALSE,
    callback_scheduled_at TIMESTAMPTZ,
    
    -- Quality
    quality_score INTEGER,  -- 1-5
    quality_notes TEXT,
    
    -- Cost tracking
    cost_cents INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_call_tasks_tenant ON call_tasks(tenant_id);
CREATE INDEX idx_call_tasks_lead ON call_tasks(lead_id);
CREATE INDEX idx_call_tasks_campaign ON call_tasks(campaign_id);
CREATE INDEX idx_call_tasks_status ON call_tasks(status);
CREATE INDEX idx_call_tasks_scheduled ON call_tasks(scheduled_at) WHERE status = 'scheduled';
CREATE INDEX idx_call_tasks_retell ON call_tasks(retell_call_id);
CREATE INDEX idx_call_tasks_created ON call_tasks(created_at DESC);

-- ============================================================================
-- TRIGGER
-- ============================================================================

CREATE TRIGGER trigger_call_tasks_updated_at
    BEFORE UPDATE ON call_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE call_tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY call_tasks_tenant_isolation ON call_tasks
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY call_tasks_service_role ON call_tasks
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE call_tasks IS 'AI call tasks for Retell AI integration';
COMMENT ON COLUMN call_tasks.retell_call_id IS 'External call ID from Retell AI';
COMMENT ON COLUMN call_tasks.outcome IS 'Call outcome: interested, not_interested, callback, meeting_booked, voicemail, wrong_number, do_not_call';
