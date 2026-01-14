-- ============================================================================
-- MIGRATION: Add assigned_agent to tenants table
-- One agent per tenant model
-- ============================================================================

-- Add assigned_agent column
ALTER TABLE tenants 
ADD COLUMN assigned_agent VARCHAR(20) DEFAULT NULL;

-- Add check constraint for valid agent values
ALTER TABLE tenants
ADD CONSTRAINT tenants_assigned_agent_check 
CHECK (assigned_agent IS NULL OR assigned_agent IN ('jules', 'joy', 'george'));

-- Add index for filtering by agent
CREATE INDEX idx_tenants_assigned_agent ON tenants(assigned_agent) 
WHERE assigned_agent IS NOT NULL;

-- Add comment
COMMENT ON COLUMN tenants.assigned_agent IS 'Assigned AI agent: jules (marketing), joy (sales), george (customer success)';
