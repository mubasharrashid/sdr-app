-- ============================================================================
-- TABLE 4: AGENTS
-- Master agent definitions (Jules, Joy, George)
-- ============================================================================

-- Create the agents table
CREATE TABLE agents (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Agent identification
    slug VARCHAR(50) UNIQUE NOT NULL,  -- jules, joy, george
    name VARCHAR(100) NOT NULL,         -- Display name
    
    -- Description & Category
    description TEXT,
    category VARCHAR(50) NOT NULL,      -- marketing, sales, customer_success
    
    -- Agent capabilities (what this agent can do)
    capabilities JSONB DEFAULT '[]',
    
    -- Default system prompt for this agent
    system_prompt TEXT,
    
    -- Default model configuration
    default_model VARCHAR(50) DEFAULT 'gpt-4',
    default_temperature DECIMAL(3,2) DEFAULT 0.7,
    
    -- Agent status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    icon_url TEXT,
    color VARCHAR(7),  -- Hex color for UI
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_agents_slug ON agents(slug);
CREATE INDEX idx_agents_category ON agents(category);
CREATE INDEX idx_agents_is_active ON agents(is_active);

-- ============================================================================
-- TRIGGER: Auto-update updated_at timestamp
-- ============================================================================

CREATE TRIGGER trigger_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SEED DATA: Insert the 3 core agents
-- ============================================================================

INSERT INTO agents (slug, name, description, category, capabilities, system_prompt, icon_url, color) VALUES
(
    'jules',
    'Jules',
    'Marketing & Lead Generation Agent - Automates outreach, generates leads, and books meetings',
    'marketing',
    '["lead_generation", "email_outreach", "linkedin_outreach", "content_generation", "campaign_management"]',
    'You are Jules, an AI marketing assistant specialized in B2B lead generation and outreach. Your goal is to help generate qualified leads and book meetings for the sales team.',
    NULL,
    '#6366F1'
),
(
    'joy',
    'Joy',
    'Sales & Deal Closing Agent - Manages deals, schedules meetings, and helps close sales',
    'sales',
    '["meeting_scheduling", "proposal_generation", "crm_management", "deal_tracking", "follow_ups"]',
    'You are Joy, an AI sales assistant specialized in B2B sales and deal management. Your goal is to help close deals and manage the sales pipeline effectively.',
    NULL,
    '#10B981'
),
(
    'george',
    'George',
    'Customer Success & Support Agent - Handles onboarding, support, and customer retention',
    'customer_success',
    '["customer_onboarding", "support_tickets", "health_scoring", "nps_tracking", "retention_campaigns"]',
    'You are George, an AI customer success assistant specialized in customer onboarding and support. Your goal is to ensure customer satisfaction and retention.',
    NULL,
    '#F59E0B'
);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE agents IS 'Master agent definitions - Jules (Marketing), Joy (Sales), George (Customer Success)';
COMMENT ON COLUMN agents.slug IS 'URL-safe identifier: jules, joy, george';
COMMENT ON COLUMN agents.capabilities IS 'JSON array of agent capabilities';
COMMENT ON COLUMN agents.system_prompt IS 'Default system prompt for AI model';
