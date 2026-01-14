-- ============================================================================
-- TABLE 12: AUDIT_LOGS
-- System-wide audit trail for compliance and debugging
-- ============================================================================

CREATE TABLE audit_logs (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Context
    tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Action details
    action VARCHAR(100) NOT NULL,  -- create, update, delete, login, logout, etc.
    resource_type VARCHAR(100) NOT NULL,  -- tenant, user, lead, campaign, etc.
    resource_id UUID,
    
    -- Change tracking
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],
    
    -- Request context
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    
    -- API context
    endpoint VARCHAR(255),
    http_method VARCHAR(10),
    response_status INTEGER,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    -- Severity/importance
    severity VARCHAR(20) DEFAULT 'info',  -- debug, info, warning, error, critical
    
    -- Timestamp (immutable)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_audit_logs_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_severity ON audit_logs(severity);
CREATE INDEX idx_audit_logs_ip ON audit_logs(ip_address);

-- Composite index for common queries
CREATE INDEX idx_audit_logs_tenant_created ON audit_logs(tenant_id, created_at DESC);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Tenants can only see their own logs
CREATE POLICY audit_logs_tenant_isolation ON audit_logs
    FOR SELECT
    USING (
        tenant_id = current_setting('app.current_tenant_id', true)::uuid
        OR tenant_id IS NULL  -- System-level logs
    );

-- Only service role can insert/update/delete
CREATE POLICY audit_logs_service_role ON audit_logs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE audit_logs IS 'System-wide audit trail for compliance and debugging';
COMMENT ON COLUMN audit_logs.action IS 'Action type: create, update, delete, login, logout, export, etc.';
COMMENT ON COLUMN audit_logs.severity IS 'Log severity: debug, info, warning, error, critical';
