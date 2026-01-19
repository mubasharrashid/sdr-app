-- ============================================================================
-- MIGRATION 009: ADD BANT QUALIFICATION TRACKING (SIMPLIFIED)
-- Adds BANT (Budget, Authority, Need, Timeline) qualification to leads
-- ============================================================================

-- Add only essential BANT columns to leads table
ALTER TABLE leads ADD COLUMN IF NOT EXISTS bant_score INTEGER DEFAULT 0 CHECK (bant_score >= 0 AND bant_score <= 12);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS bant_status VARCHAR(30) DEFAULT 'unqualified' CHECK (bant_status IN ('unqualified', 'partially_qualified', 'qualified'));
ALTER TABLE leads ADD COLUMN IF NOT EXISTS bant_data JSONB DEFAULT '{}';
ALTER TABLE leads ADD COLUMN IF NOT EXISTS bant_sales_notes TEXT;

-- Add BANT tracking to leads_ai_conversation
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS bant_data JSONB DEFAULT '{}';

-- Index for filtering by BANT status
CREATE INDEX IF NOT EXISTS idx_leads_bant_status ON leads(bant_status);

-- Comments
COMMENT ON COLUMN leads.bant_score IS 'Overall BANT score (0-12)';
COMMENT ON COLUMN leads.bant_status IS 'BANT qualification: unqualified (0-3), partially_qualified (4-7), qualified (8-12)';
COMMENT ON COLUMN leads.bant_data IS 'Full BANT details as JSON: {budget: {}, authority: {}, need: {}, timeline: {}}';
COMMENT ON COLUMN leads.bant_sales_notes IS 'BANT summary notes for sales team';
