-- ============================================================================
-- TABLE 11: AGENT_EXECUTIONS
-- Track each agent task execution with full context
-- ============================================================================

CREATE TABLE agent_executions (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    tenant_agent_id UUID REFERENCES tenant_agents(id) ON DELETE SET NULL,
    
    -- Execution context
    workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
    triggered_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Task identification
    task_type VARCHAR(100) NOT NULL,  -- email_draft, lead_research, call_prep, etc.
    task_name VARCHAR(255),
    
    -- Input/Output
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    
    -- Execution status
    status VARCHAR(20) DEFAULT 'pending',  -- pending, running, completed, failed, cancelled
    error_message TEXT,
    error_details JSONB,
    
    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    
    -- AI/LLM metrics
    model_used VARCHAR(100),
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    estimated_cost NUMERIC(10, 6) DEFAULT 0,
    
    -- Crew AI specific
    crew_run_id VARCHAR(100),
    crew_steps JSONB DEFAULT '[]',
    
    -- Related entities
    lead_id UUID,  -- Will reference leads table
    campaign_id UUID,  -- Will reference campaigns table
    
    -- Quality metrics
    confidence_score NUMERIC(3, 2),
    quality_rating INTEGER,  -- 1-5 user rating
    feedback TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_agent_executions_tenant ON agent_executions(tenant_id);
CREATE INDEX idx_agent_executions_agent ON agent_executions(agent_id);
CREATE INDEX idx_agent_executions_status ON agent_executions(status);
CREATE INDEX idx_agent_executions_task_type ON agent_executions(task_type);
CREATE INDEX idx_agent_executions_created ON agent_executions(created_at DESC);
CREATE INDEX idx_agent_executions_workflow ON agent_executions(workflow_id);
CREATE INDEX idx_agent_executions_lead ON agent_executions(lead_id);
CREATE INDEX idx_agent_executions_campaign ON agent_executions(campaign_id);

-- ============================================================================
-- TRIGGER
-- ============================================================================

CREATE TRIGGER trigger_agent_executions_updated_at
    BEFORE UPDATE ON agent_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE agent_executions ENABLE ROW LEVEL SECURITY;

CREATE POLICY agent_executions_tenant_isolation ON agent_executions
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY agent_executions_service_role ON agent_executions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE agent_executions IS 'Track each agent task execution with full context';
COMMENT ON COLUMN agent_executions.task_type IS 'Type of task: email_draft, lead_research, call_prep, etc.';
COMMENT ON COLUMN agent_executions.crew_steps IS 'Crew AI execution steps and reasoning';
