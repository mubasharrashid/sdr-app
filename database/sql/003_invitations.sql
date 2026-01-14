-- ============================================================================
-- TABLE 3: INVITATIONS
-- User invitation system for multi-tenant platform
-- ============================================================================

-- Create the invitations table
CREATE TABLE invitations (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Tenant relationship
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Invitation details
    email VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'member',  -- owner, admin, member
    
    -- Token for secure acceptance
    token VARCHAR(255) UNIQUE NOT NULL,
    
    -- Inviter information
    invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending',  -- pending, accepted, expired, cancelled
    
    -- Expiration
    expires_at TIMESTAMPTZ NOT NULL,
    
    -- Acceptance tracking
    accepted_at TIMESTAMPTZ,
    accepted_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Optional message from inviter
    message TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT invitations_email_tenant_unique UNIQUE (tenant_id, email, status)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Lookup invitation by token (for acceptance)
CREATE INDEX idx_invitations_token ON invitations(token);

-- List invitations by tenant
CREATE INDEX idx_invitations_tenant ON invitations(tenant_id);

-- Lookup by email (for checking existing invites)
CREATE INDEX idx_invitations_email ON invitations(email);

-- Filter by status
CREATE INDEX idx_invitations_status ON invitations(status);

-- Find expired invitations for cleanup
CREATE INDEX idx_invitations_expires ON invitations(expires_at) 
    WHERE status = 'pending';

-- ============================================================================
-- TRIGGER: Auto-update updated_at timestamp
-- ============================================================================

CREATE TRIGGER trigger_invitations_updated_at
    BEFORE UPDATE ON invitations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS
ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see invitations in their own tenant
CREATE POLICY invitations_tenant_isolation ON invitations
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Policy: Service role bypasses RLS
CREATE POLICY invitations_service_role ON invitations
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE invitations IS 'User invitations - allows existing users to invite new users to their tenant';
COMMENT ON COLUMN invitations.token IS 'Unique secure token for invitation acceptance';
COMMENT ON COLUMN invitations.role IS 'Role the invited user will have: owner, admin, member';
COMMENT ON COLUMN invitations.status IS 'Invitation status: pending, accepted, expired, cancelled';
COMMENT ON COLUMN invitations.expires_at IS 'Invitation expiration timestamp (typically 7 days from creation)';
