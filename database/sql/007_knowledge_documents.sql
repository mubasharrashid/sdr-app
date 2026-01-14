-- ============================================================================
-- TABLE 7: KNOWLEDGE_DOCUMENTS
-- Individual documents uploaded to knowledge bases
-- ============================================================================

CREATE TABLE knowledge_documents (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Document details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- File information
    file_type VARCHAR(50),  -- pdf, docx, txt, csv, html, md
    file_size INTEGER,      -- Size in bytes
    file_url TEXT,          -- S3/storage URL
    original_filename VARCHAR(255),
    
    -- Content
    content_text TEXT,      -- Extracted text content
    content_hash VARCHAR(64),  -- SHA256 hash for deduplication
    
    -- Processing status
    status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, ready, failed
    processing_error TEXT,
    
    -- Chunking information
    chunk_count INTEGER DEFAULT 0,
    
    -- Vector IDs (for deletion from Pinecone)
    vector_ids JSONB DEFAULT '[]',
    
    -- Metadata extracted from document
    metadata JSONB DEFAULT '{}',
    
    -- Upload tracking
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Timestamps
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_knowledge_documents_kb ON knowledge_documents(knowledge_base_id);
CREATE INDEX idx_knowledge_documents_tenant ON knowledge_documents(tenant_id);
CREATE INDEX idx_knowledge_documents_status ON knowledge_documents(status);
CREATE INDEX idx_knowledge_documents_hash ON knowledge_documents(content_hash);
CREATE INDEX idx_knowledge_documents_type ON knowledge_documents(file_type);

-- ============================================================================
-- TRIGGER
-- ============================================================================

CREATE TRIGGER trigger_knowledge_documents_updated_at
    BEFORE UPDATE ON knowledge_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE knowledge_documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY knowledge_documents_tenant_isolation ON knowledge_documents
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY knowledge_documents_service_role ON knowledge_documents
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE knowledge_documents IS 'Documents uploaded to knowledge bases for RAG';
COMMENT ON COLUMN knowledge_documents.file_url IS 'S3 or cloud storage URL';
COMMENT ON COLUMN knowledge_documents.content_hash IS 'SHA256 hash for deduplication';
COMMENT ON COLUMN knowledge_documents.vector_ids IS 'Array of vector IDs in Pinecone for cleanup';
