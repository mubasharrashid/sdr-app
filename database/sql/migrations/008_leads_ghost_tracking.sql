-- ============================================================================
-- Migration: Add Ghost Tracking Fields to Leads
-- ============================================================================
-- Enables tracking of AI conversation state and ghost detection
-- ============================================================================

-- Conversation state (separate from outreach_status)
-- Tracks where the lead is in the AI conversation flow
ALTER TABLE leads ADD COLUMN IF NOT EXISTS conversation_state VARCHAR(30) DEFAULT 'in_sequence';

-- Add check constraint for valid states
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'leads_conversation_state_check'
    ) THEN
        ALTER TABLE leads ADD CONSTRAINT leads_conversation_state_check 
        CHECK (conversation_state IN ('in_sequence', 'engaged', 'awaiting_reply', 'ghosted'));
    END IF;
END $$;

-- When did AI last send a response to this lead
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ai_last_response_at TIMESTAMPTZ;

-- What step was the lead on when they engaged (to resume from after ghost)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS sequence_paused_at_step INTEGER;

-- How long to wait before considering them ghosted (in hours)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ghost_timeout_hours INTEGER DEFAULT 48;

-- Count of re-engagement attempts after ghosting
ALTER TABLE leads ADD COLUMN IF NOT EXISTS re_engagement_count INTEGER DEFAULT 0;

-- Maximum re-engagement attempts before giving up
ALTER TABLE leads ADD COLUMN IF NOT EXISTS max_re_engagements INTEGER DEFAULT 5;

-- Index for ghost detection query (finds leads awaiting reply past timeout)
CREATE INDEX IF NOT EXISTS idx_leads_ghost_detection 
ON leads(conversation_state, ai_last_response_at) 
WHERE conversation_state = 'awaiting_reply';

-- Index for re-engagement eligible leads
CREATE INDEX IF NOT EXISTS idx_leads_reengagement_eligible
ON leads(conversation_state, re_engagement_count, max_re_engagements)
WHERE conversation_state = 'awaiting_reply';

-- Comments
COMMENT ON COLUMN leads.conversation_state IS 'AI conversation state: in_sequence, engaged, awaiting_reply, ghosted';
COMMENT ON COLUMN leads.ai_last_response_at IS 'Timestamp when AI last sent a response to this lead';
COMMENT ON COLUMN leads.sequence_paused_at_step IS 'The step number when lead engaged (to resume from after ghost)';
COMMENT ON COLUMN leads.ghost_timeout_hours IS 'Hours to wait before considering lead as ghosted (default 48)';
COMMENT ON COLUMN leads.re_engagement_count IS 'Number of times we have re-engaged this lead after ghosting';
COMMENT ON COLUMN leads.max_re_engagements IS 'Maximum re-engagement attempts before stopping (default 5)';
