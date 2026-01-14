-- ============================================================================
-- TABLE 8: INTEGRATIONS
-- Master list of available third-party integrations
-- ============================================================================

CREATE TABLE integrations (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Integration identification
    slug VARCHAR(50) UNIQUE NOT NULL,  -- gmail, hubspot, slack, etc.
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Categorization
    category VARCHAR(50) NOT NULL,  -- email, crm, communication, calendar, etc.
    
    -- Provider information
    provider VARCHAR(100),
    provider_url TEXT,
    
    -- Authentication type
    auth_type VARCHAR(20) NOT NULL,  -- oauth2, api_key, basic, webhook
    
    -- OAuth configuration (if applicable)
    oauth_authorization_url TEXT,
    oauth_token_url TEXT,
    oauth_scopes TEXT[],
    
    -- Required credentials fields (for API key auth)
    required_fields JSONB DEFAULT '[]',
    
    -- UI metadata
    icon_url TEXT,
    color VARCHAR(7),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_premium BOOLEAN DEFAULT FALSE,
    
    -- Documentation
    docs_url TEXT,
    setup_instructions TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_integrations_slug ON integrations(slug);
CREATE INDEX idx_integrations_category ON integrations(category);
CREATE INDEX idx_integrations_is_active ON integrations(is_active);

-- ============================================================================
-- TRIGGER
-- ============================================================================

CREATE TRIGGER trigger_integrations_updated_at
    BEFORE UPDATE ON integrations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- SEED DATA: Core integrations
-- ============================================================================

INSERT INTO integrations (slug, name, description, category, auth_type, is_active) VALUES
('gmail', 'Gmail', 'Send and receive emails via Gmail', 'email', 'oauth2', true),
('outlook', 'Microsoft Outlook', 'Send and receive emails via Outlook', 'email', 'oauth2', true),
('hubspot', 'HubSpot', 'CRM integration for lead and deal management', 'crm', 'oauth2', true),
('salesforce', 'Salesforce', 'CRM integration for enterprise sales', 'crm', 'oauth2', true),
('slack', 'Slack', 'Team notifications and alerts', 'communication', 'oauth2', true),
('google_calendar', 'Google Calendar', 'Meeting scheduling', 'calendar', 'oauth2', true),
('calendly', 'Calendly', 'Appointment scheduling', 'calendar', 'api_key', true),
('linkedin', 'LinkedIn', 'Professional networking and outreach', 'social', 'oauth2', true),
('apollo', 'Apollo.io', 'Lead enrichment and prospecting', 'enrichment', 'api_key', true),
('retell', 'Retell AI', 'AI-powered phone calls', 'voice', 'api_key', true),
('openai', 'OpenAI', 'AI/LLM provider', 'ai', 'api_key', true),
('pinecone', 'Pinecone', 'Vector database for RAG', 'database', 'api_key', true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE integrations IS 'Master list of available third-party integrations';
COMMENT ON COLUMN integrations.auth_type IS 'Authentication type: oauth2, api_key, basic, webhook';
COMMENT ON COLUMN integrations.required_fields IS 'JSON array of required credential field names';
