-- ============================================================================
-- TABLE 13: API_KEYS
-- API key management for external access
-- ============================================================================

CREATE TABLE api_keys (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Ownership
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Key identification
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Key data (hashed for security)
    key_prefix VARCHAR(10) NOT NULL,  -- First 8 chars for identification
    key_hash VARCHAR(255) NOT NULL,  -- Hashed full key
    
    -- Permissions
    scopes TEXT[] DEFAULT ARRAY['read'],  -- read, write, admin, etc.
    allowed_ips INET[],  -- IP whitelist (null = all IPs allowed)
    
    -- Rate limiting
    rate_limit INTEGER DEFAULT 1000,  -- Requests per hour
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Expiration
    expires_at TIMESTAMPTZ,
    
    -- Usage tracking
    last_used_at TIMESTAMPTZ,
    usage_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    revoked_by UUID REFERENCES users(id) ON DELETE SET NULL,
    revoke_reason TEXT
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id);
CREATE INDEX idx_api_keys_prefix ON api_keys(key_prefix);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_active ON api_keys(is_active) WHERE is_active = true;
CREATE INDEX idx_api_keys_expires ON api_keys(expires_at) WHERE expires_at IS NOT NULL;

-- ============================================================================
-- TRIGGER
-- ============================================================================

CREATE TRIGGER trigger_api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY api_keys_tenant_isolation ON api_keys
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY api_keys_service_role ON api_keys
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE api_keys IS 'API key management for external access';
COMMENT ON COLUMN api_keys.key_prefix IS 'First 8 characters of key for identification';
COMMENT ON COLUMN api_keys.key_hash IS 'SHA-256 hash of the full API key';
COMMENT ON COLUMN api_keys.scopes IS 'Allowed scopes: read, write, admin, leads, campaigns, etc.';
