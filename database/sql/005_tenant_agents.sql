-- ============================================================================
-- TABLE 5: TENANT_AGENTS
-- Junction table linking tenants to their assigned agents
-- Supports one-agent-per-tenant with per-tenant customization
-- ============================================================================

CREATE TABLE tenant_agents (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Per-tenant customization
    custom_system_prompt TEXT,
    custom_model VARCHAR(50),
    custom_temperature DECIMAL(3,2),
    
    -- Agent-specific settings for this tenant
    settings JSONB DEFAULT '{}',
    
    -- Usage tracking
    total_executions INTEGER DEFAULT 0,
    last_execution_at TIMESTAMPTZ,
    
    -- Timestamps
    activated_at TIMESTAMPTZ DEFAULT NOW(),
    deactivated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT tenant_agents_unique UNIQUE (tenant_id, agent_id)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- List agents by tenant
CREATE INDEX idx_tenant_agents_tenant ON tenant_agents(tenant_id);

-- List tenants by agent
CREATE INDEX idx_tenant_agents_agent ON tenant_agents(agent_id);

-- Find active assignments
CREATE INDEX idx_tenant_agents_active ON tenant_agents(tenant_id, is_active) 
WHERE is_active = TRUE;

-- ============================================================================
-- TRIGGER: Auto-update updated_at timestamp
-- ============================================================================

CREATE TRIGGER trigger_tenant_agents_updated_at
    BEFORE UPDATE ON tenant_agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE tenant_agents ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_agents_tenant_isolation ON tenant_agents
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY tenant_agents_service_role ON tenant_agents
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE tenant_agents IS 'Links tenants to their assigned AI agents with per-tenant customization';
COMMENT ON COLUMN tenant_agents.custom_system_prompt IS 'Override the agent default system prompt for this tenant';
COMMENT ON COLUMN tenant_agents.settings IS 'Tenant-specific agent settings (JSON)';
