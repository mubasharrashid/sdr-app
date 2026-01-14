-- ============================================================================
-- TABLE 10: WORKFLOWS
-- n8n workflow references and automation definitions
-- ============================================================================

CREATE TABLE workflows (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    
    -- Workflow identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- n8n reference
    n8n_workflow_id VARCHAR(100),
    n8n_webhook_url TEXT,
    
    -- Workflow type
    workflow_type VARCHAR(50) NOT NULL,  -- trigger, action, scheduled, manual
    trigger_event VARCHAR(100),  -- lead_created, email_received, meeting_booked, etc.
    
    -- Configuration
    config JSONB DEFAULT '{}',
    input_schema JSONB DEFAULT '{}',
    output_schema JSONB DEFAULT '{}',
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft',  -- draft, active, paused, archived
    is_enabled BOOLEAN DEFAULT TRUE,
    
    -- Execution tracking
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    last_executed_at TIMESTAMPTZ,
    last_error TEXT,
    
    -- Scheduling (for scheduled workflows)
    schedule_cron VARCHAR(100),
    next_scheduled_at TIMESTAMPTZ,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_workflows_tenant ON workflows(tenant_id);
CREATE INDEX idx_workflows_agent ON workflows(agent_id);
CREATE INDEX idx_workflows_type ON workflows(workflow_type);
CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_trigger ON workflows(trigger_event);
CREATE INDEX idx_workflows_n8n ON workflows(n8n_workflow_id);

-- ============================================================================
-- TRIGGER
-- ============================================================================

CREATE TRIGGER trigger_workflows_updated_at
    BEFORE UPDATE ON workflows
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;

CREATE POLICY workflows_tenant_isolation ON workflows
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY workflows_service_role ON workflows
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE workflows IS 'n8n workflow references and automation definitions';
COMMENT ON COLUMN workflows.n8n_workflow_id IS 'External n8n workflow ID';
COMMENT ON COLUMN workflows.trigger_event IS 'Event that triggers this workflow';
COMMENT ON COLUMN workflows.schedule_cron IS 'Cron expression for scheduled workflows';
