-- ============================================================================
-- TABLE 20: MEETINGS
-- Meeting bookings and tracking
-- ============================================================================

CREATE TABLE meetings (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Relationships
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    booked_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Meeting details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    meeting_type VARCHAR(50),  -- discovery, demo, follow_up, closing, other
    
    -- Scheduling
    scheduled_at TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Location/Link
    location VARCHAR(255),
    meeting_url TEXT,
    meeting_platform VARCHAR(50),  -- zoom, google_meet, teams, calendly, in_person
    
    -- Attendees
    attendees JSONB DEFAULT '[]',  -- [{email, name, status}]
    
    -- Status
    status VARCHAR(30) DEFAULT 'scheduled',  -- scheduled, confirmed, completed, cancelled, no_show, rescheduled
    
    -- Calendar sync
    calendar_event_id VARCHAR(255),
    calendar_provider VARCHAR(50),  -- google, outlook, calendly
    
    -- How was it booked
    booking_source VARCHAR(50),  -- ai_call, email_reply, calendly, manual
    
    -- Pre-meeting
    prep_notes TEXT,
    ai_prep_summary TEXT,
    
    -- Post-meeting
    meeting_notes TEXT,
    outcome VARCHAR(50),  -- positive, neutral, negative
    next_steps TEXT,
    follow_up_date DATE,
    
    -- Recording
    recording_url TEXT,
    transcript TEXT,
    
    -- Reminders
    reminder_sent BOOLEAN DEFAULT FALSE,
    reminder_sent_at TIMESTAMPTZ,
    
    -- Timestamps
    confirmed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_meetings_tenant ON meetings(tenant_id);
CREATE INDEX idx_meetings_lead ON meetings(lead_id);
CREATE INDEX idx_meetings_campaign ON meetings(campaign_id);
CREATE INDEX idx_meetings_scheduled ON meetings(scheduled_at);
CREATE INDEX idx_meetings_status ON meetings(status);
CREATE INDEX idx_meetings_calendar ON meetings(calendar_event_id);
CREATE INDEX idx_meetings_upcoming ON meetings(scheduled_at) 
    WHERE status IN ('scheduled', 'confirmed');

-- ============================================================================
-- TRIGGER
-- ============================================================================

CREATE TRIGGER trigger_meetings_updated_at
    BEFORE UPDATE ON meetings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE meetings ENABLE ROW LEVEL SECURITY;

CREATE POLICY meetings_tenant_isolation ON meetings
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);

CREATE POLICY meetings_service_role ON meetings
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE meetings IS 'Meeting bookings and tracking';
COMMENT ON COLUMN meetings.status IS 'Meeting status: scheduled, confirmed, completed, cancelled, no_show, rescheduled';
COMMENT ON COLUMN meetings.booking_source IS 'How meeting was booked: ai_call, email_reply, calendly, manual';
