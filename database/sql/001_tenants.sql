-- ============================================================================
-- TABLE 1: TENANTS
-- Multi-tenant foundation table for B2B SaaS platform
-- ============================================================================

-- Create the tenants table
CREATE TABLE tenants (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Basic Information
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    logo_url TEXT,
    primary_color VARCHAR(7),  -- Hex color code like #FF5733
    
    -- Contact Information
    email VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(255),
    
    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Subscription & Billing
    plan VARCHAR(50) DEFAULT 'free',  -- free, starter, pro, enterprise
    plan_started_at TIMESTAMPTZ,
    plan_expires_at TIMESTAMPTZ,
    billing_email VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    
    -- Usage Limits
    max_users INTEGER DEFAULT 5,
    max_leads INTEGER DEFAULT 1000,
    max_emails_per_day INTEGER DEFAULT 100,
    max_calls_per_day INTEGER DEFAULT 50,
    
    -- Status & Settings
    status VARCHAR(20) DEFAULT 'active',  -- active, suspended, cancelled
    suspended_reason TEXT,
    settings JSONB DEFAULT '{}',
    
    -- Timestamps
    onboarded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Primary lookup by slug (used in URL routing)
CREATE INDEX idx_tenants_slug ON tenants(slug);

-- Filter by status (for admin dashboards)
CREATE INDEX idx_tenants_status ON tenants(status);

-- Filter by plan (for billing reports)
CREATE INDEX idx_tenants_plan ON tenants(plan);

-- Stripe customer lookup (for webhooks)
CREATE INDEX idx_tenants_stripe ON tenants(stripe_customer_id) 
    WHERE stripe_customer_id IS NOT NULL;

-- ============================================================================
-- TRIGGER: Auto-update updated_at timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE tenants IS 'Multi-tenant foundation table - each row represents a client company';
COMMENT ON COLUMN tenants.slug IS 'URL-safe unique identifier (e.g., acme-corp)';
COMMENT ON COLUMN tenants.plan IS 'Subscription tier: free, starter, pro, enterprise';
COMMENT ON COLUMN tenants.status IS 'Account status: active, suspended, cancelled';
COMMENT ON COLUMN tenants.settings IS 'Flexible JSON for tenant-specific configuration';
