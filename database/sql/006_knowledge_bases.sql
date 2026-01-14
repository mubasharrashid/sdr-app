-- ============================================================================
-- TABLE 6: KNOWLEDGE_BASES
-- Knowledge base containers for RAG (per tenant/agent)
-- ============================================================================

CREATE TABLE knowledge_bases (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    
    -- Knowledge base details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Type of knowledge base
    kb_type VARCHAR(50) DEFAULT 'general',  -- general, product, faq, competitor, industry
    
    -- Vector database configuration
    vector_index_name VARCHAR(255),  -- Pinecone index name
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small',
    chunk_size INTEGER DEFAULT 500,
    chunk_overlap INTEGER DEFAULT 50,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- active, processing, inactive
    
    -- Statistics
    document_count INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    last_synced_at TIMESTAMPTZ,
    
    -- Settings
    settings JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_knowledge_bases_tenant ON knowledge_bases(tenant_id);
CREATE INDEX idx_knowledge_bases_agent ON knowledge_bases(agent_id);
CREATE INDEX idx_knowledge_bases_status ON knowledge_bases(status);
CREATE INDEX idx_knowledge_bases_type ON knowledge_bases(kb_type);

-- ============================================================================
-- TRIGGER
-- ============================================================================

CREATE TRIGGER trigger_knowledge_bases_updated_at
    BEFORE UPDATE ON knowledge_bases
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE knowledge_bases ENABLE ROW LEVEL SECURITY;

CREATE POLICY knowledge_bases_tenant_isolation ON knowledge_bases
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY knowledge_bases_service_role ON knowledge_bases
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE knowledge_bases IS 'Knowledge base containers for RAG - stores documents for AI agent reference';
COMMENT ON COLUMN knowledge_bases.kb_type IS 'Type: general, product, faq, competitor, industry';
COMMENT ON COLUMN knowledge_bases.vector_index_name IS 'Pinecone or vector DB index name';
COMMENT ON COLUMN knowledge_bases.embedding_model IS 'OpenAI embedding model used';
