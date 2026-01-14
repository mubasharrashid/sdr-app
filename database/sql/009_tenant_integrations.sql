-- ============================================================================
-- TABLE 9: TENANT_INTEGRATIONS
-- OAuth tokens and credentials per tenant
-- ============================================================================

CREATE TABLE tenant_integrations (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    
    -- Connection status
    status VARCHAR(20) DEFAULT 'pending',  -- pending, connected, expired, error
    
    -- OAuth tokens (encrypted in production)
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMPTZ,
    
    -- API credentials (for non-OAuth integrations)
    credentials JSONB DEFAULT '{}',
    
    -- OAuth metadata
    oauth_account_id TEXT,  -- External account ID
    oauth_account_email TEXT,
    oauth_scopes TEXT[],
    
    -- Configuration
    settings JSONB DEFAULT '{}',
    
    -- Usage tracking
    last_used_at TIMESTAMPTZ,
    last_sync_at TIMESTAMPTZ,
    error_message TEXT,
    error_count INTEGER DEFAULT 0,
    
    -- Connected by
    connected_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Timestamps
    connected_at TIMESTAMPTZ,
    disconnected_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT tenant_integrations_unique UNIQUE (tenant_id, integration_id)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_tenant_integrations_tenant ON tenant_integrations(tenant_id);
CREATE INDEX idx_tenant_integrations_integration ON tenant_integrations(integration_id);
CREATE INDEX idx_tenant_integrations_status ON tenant_integrations(status);
CREATE INDEX idx_tenant_integrations_expires ON tenant_integrations(token_expires_at) 
WHERE status = 'connected';

-- ============================================================================
-- TRIGGER
-- ============================================================================

CREATE TRIGGER trigger_tenant_integrations_updated_at
    BEFORE UPDATE ON tenant_integrations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE tenant_integrations ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_integrations_tenant_isolation ON tenant_integrations
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY tenant_integrations_service_role ON tenant_integrations
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE tenant_integrations IS 'OAuth tokens and credentials per tenant';
COMMENT ON COLUMN tenant_integrations.credentials IS 'Encrypted API credentials for non-OAuth integrations';
COMMENT ON COLUMN tenant_integrations.settings IS 'Integration-specific settings per tenant';
