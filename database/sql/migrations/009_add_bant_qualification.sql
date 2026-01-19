-- ============================================================================
-- MIGRATION 009: ADD BANT QUALIFICATION TRACKING
-- Adds BANT (Budget, Authority, Need, Timeline) qualification fields to leads
-- ============================================================================

-- ============================================================================
-- ADD BANT COLUMNS TO LEADS TABLE
-- ============================================================================

-- BANT qualification scores (0-3 each, 0-12 total)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS bant_budget_score INTEGER DEFAULT 0 CHECK (bant_budget_score >= 0 AND bant_budget_score <= 3);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS bant_authority_score INTEGER DEFAULT 0 CHECK (bant_authority_score >= 0 AND bant_authority_score <= 3);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS bant_need_score INTEGER DEFAULT 0 CHECK (bant_need_score >= 0 AND bant_need_score <= 3);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS bant_timeline_score INTEGER DEFAULT 0 CHECK (bant_timeline_score >= 0 AND bant_timeline_score <= 3);

-- BANT details (text descriptions of what was identified)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS bant_budget_details TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS bant_authority_details TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS bant_need_details TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS bant_timeline_details TEXT;

-- Overall BANT score and status
ALTER TABLE leads ADD COLUMN IF NOT EXISTS bant_overall_score INTEGER DEFAULT 0 CHECK (bant_overall_score >= 0 AND bant_overall_score <= 12);
ALTER TABLE leads ADD COLUMN IF NOT EXISTS bant_qualification_status VARCHAR(30) DEFAULT 'unqualified' CHECK (bant_qualification_status IN ('unqualified', 'partially_qualified', 'qualified'));

-- BANT notes for sales team
ALTER TABLE leads ADD COLUMN IF NOT EXISTS bant_sales_notes TEXT;

-- Last BANT update timestamp
ALTER TABLE leads ADD COLUMN IF NOT EXISTS bant_updated_at TIMESTAMPTZ;

-- ============================================================================
-- CREATE FUNCTION TO UPDATE BANT OVERALL SCORE
-- ============================================================================

CREATE OR REPLACE FUNCTION update_bant_overall_score()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate overall score
    NEW.bant_overall_score := COALESCE(NEW.bant_budget_score, 0) + 
                              COALESCE(NEW.bant_authority_score, 0) + 
                              COALESCE(NEW.bant_need_score, 0) + 
                              COALESCE(NEW.bant_timeline_score, 0);
    
    -- Determine qualification status based on overall score
    IF NEW.bant_overall_score >= 8 THEN
        NEW.bant_qualification_status := 'qualified';
    ELSIF NEW.bant_overall_score >= 4 THEN
        NEW.bant_qualification_status := 'partially_qualified';
    ELSE
        NEW.bant_qualification_status := 'unqualified';
    END IF;
    
    -- Update timestamp
    NEW.bant_updated_at := NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- CREATE TRIGGER FOR BANT SCORE CALCULATION
-- ============================================================================

DROP TRIGGER IF EXISTS trigger_leads_bant_score ON leads;

CREATE TRIGGER trigger_leads_bant_score
    BEFORE INSERT OR UPDATE OF bant_budget_score, bant_authority_score, bant_need_score, bant_timeline_score
    ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_bant_overall_score();

-- ============================================================================
-- ADD INDEX FOR BANT FILTERING
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_leads_bant_status ON leads(bant_qualification_status);
CREATE INDEX IF NOT EXISTS idx_leads_bant_score ON leads(bant_overall_score DESC);

-- ============================================================================
-- ADD BANT FIELDS TO LEADS_AI_CONVERSATION FOR TRACKING PER MESSAGE
-- ============================================================================

ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS bant_budget_identified BOOLEAN DEFAULT FALSE;
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS bant_authority_identified BOOLEAN DEFAULT FALSE;
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS bant_need_identified BOOLEAN DEFAULT FALSE;
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS bant_timeline_identified BOOLEAN DEFAULT FALSE;
ALTER TABLE leads_ai_conversation ADD COLUMN IF NOT EXISTS bant_data JSONB DEFAULT '{}';

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN leads.bant_budget_score IS 'BANT Budget score: 0=not identified, 1=partially, 2=identified, 3=confirmed';
COMMENT ON COLUMN leads.bant_authority_score IS 'BANT Authority score: 0=not identified, 1=partially, 2=identified, 3=confirmed';
COMMENT ON COLUMN leads.bant_need_score IS 'BANT Need score: 0=not identified, 1=partially, 2=identified, 3=confirmed';
COMMENT ON COLUMN leads.bant_timeline_score IS 'BANT Timeline score: 0=not identified, 1=partially, 2=identified, 3=confirmed';
COMMENT ON COLUMN leads.bant_overall_score IS 'Total BANT score (0-12)';
COMMENT ON COLUMN leads.bant_qualification_status IS 'BANT qualification: unqualified (0-3), partially_qualified (4-7), qualified (8-12)';
COMMENT ON COLUMN leads.bant_sales_notes IS 'BANT summary notes for sales team before meetings';
