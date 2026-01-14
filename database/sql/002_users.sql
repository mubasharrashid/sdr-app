-- ============================================================================
-- TABLE 2: USERS
-- User accounts for the multi-tenant platform
-- ============================================================================

-- Create the users table
CREATE TABLE users (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Tenant relationship (multi-tenancy)
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Authentication
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Profile Information
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    phone VARCHAR(50),
    job_title VARCHAR(100),
    
    -- Role & Permissions
    role VARCHAR(20) DEFAULT 'member',  -- owner, admin, member
    permissions JSONB DEFAULT '[]',
    
    -- Account Status
    status VARCHAR(20) DEFAULT 'active',  -- active, inactive, suspended
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMPTZ,
    
    -- Security
    last_login_at TIMESTAMPTZ,
    last_login_ip VARCHAR(45),
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ,
    
    -- Preferences
    timezone VARCHAR(50),
    locale VARCHAR(10) DEFAULT 'en',
    preferences JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT users_email_tenant_unique UNIQUE (tenant_id, email)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Lookup user by email within a tenant
CREATE INDEX idx_users_tenant_email ON users(tenant_id, email);

-- List users by tenant
CREATE INDEX idx_users_tenant ON users(tenant_id);

-- Filter by role (for permission checks)
CREATE INDEX idx_users_role ON users(role);

-- Filter by status
CREATE INDEX idx_users_status ON users(status);

-- Email lookup (for global auth - without tenant context)
CREATE INDEX idx_users_email ON users(email);

-- ============================================================================
-- TRIGGER: Auto-update updated_at timestamp
-- ============================================================================

CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see users in their own tenant
CREATE POLICY users_tenant_isolation ON users
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

-- Policy: Service role bypasses RLS (for admin operations)
CREATE POLICY users_service_role ON users
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE users IS 'User accounts - each user belongs to exactly one tenant';
COMMENT ON COLUMN users.tenant_id IS 'Foreign key to tenants table for multi-tenancy';
COMMENT ON COLUMN users.role IS 'User role: owner (full access), admin (manage users), member (basic access)';
COMMENT ON COLUMN users.permissions IS 'Array of specific permissions for fine-grained access control';
COMMENT ON COLUMN users.preferences IS 'User-specific settings and preferences';
