-- ============================================================================
-- MIGRATION: Rename meeting_booked to meetings and add multi-tenant support
-- ============================================================================

-- Step 1: Rename the table from meeting_booked to meetings
ALTER TABLE IF EXISTS meeting_booked RENAME TO meetings;

-- Step 2: Add tenant_id column (required for multi-tenancy)
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;

-- Step 3: Add/ensure lead_id relationship
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS lead_id UUID REFERENCES leads(id) ON DELETE CASCADE;

-- Step 4: Add campaign relationship
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS booked_by UUID REFERENCES users(id) ON DELETE SET NULL;

-- Step 5: Add meeting details
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS meeting_type VARCHAR(50);

-- Step 6: Add scheduling fields
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMPTZ;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS duration_minutes INTEGER DEFAULT 30;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC';

-- Step 7: Add location/link
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS location VARCHAR(255);
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS meeting_url TEXT;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS meeting_platform VARCHAR(50);

-- Step 8: Add attendees
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS attendees JSONB DEFAULT '[]';

-- Step 9: Add status
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'scheduled';

-- Step 10: Add calendar sync
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS calendar_event_id VARCHAR(255);
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS calendar_provider VARCHAR(50);

-- Step 11: Add booking source
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS booking_source VARCHAR(50);

-- Step 12: Add pre-meeting notes
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS prep_notes TEXT;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS ai_prep_summary TEXT;

-- Step 13: Add post-meeting fields
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS meeting_notes TEXT;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS outcome VARCHAR(50);
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS next_steps TEXT;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS follow_up_date DATE;

-- Step 14: Add recording
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS recording_url TEXT;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS transcript TEXT;

-- Step 15: Add reminders
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS reminder_sent BOOLEAN DEFAULT FALSE;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS reminder_sent_at TIMESTAMPTZ;

-- Step 16: Add timestamps
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMPTZ;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ;
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE meetings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_meetings_tenant ON meetings(tenant_id);
CREATE INDEX IF NOT EXISTS idx_meetings_lead ON meetings(lead_id);
CREATE INDEX IF NOT EXISTS idx_meetings_campaign ON meetings(campaign_id);
CREATE INDEX IF NOT EXISTS idx_meetings_scheduled ON meetings(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_meetings_status ON meetings(status);
CREATE INDEX IF NOT EXISTS idx_meetings_calendar ON meetings(calendar_event_id);

-- ============================================================================
-- TRIGGER
-- ============================================================================

DROP TRIGGER IF EXISTS trigger_meetings_updated_at ON meetings;
CREATE TRIGGER trigger_meetings_updated_at
    BEFORE UPDATE ON meetings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS meetings_tenant_isolation ON meetings;
CREATE POLICY meetings_tenant_isolation ON meetings
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

DROP POLICY IF EXISTS meetings_service_role ON meetings;
CREATE POLICY meetings_service_role ON meetings
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE meetings IS 'Meeting bookings and tracking (renamed from meeting_booked)';
