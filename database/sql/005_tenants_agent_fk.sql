-- ============================================================================
-- MIGRATION: Add assigned_agent_id to tenants (Foreign Key to agents table)
-- Run this AFTER 004_agents.sql
-- ============================================================================

-- Add assigned_agent_id column with foreign key
ALTER TABLE tenants 
ADD COLUMN assigned_agent_id UUID REFERENCES agents(id) ON DELETE SET NULL;

-- Add index for filtering
CREATE INDEX idx_tenants_assigned_agent_id ON tenants(assigned_agent_id) 
WHERE assigned_agent_id IS NOT NULL;

-- Add comment
COMMENT ON COLUMN tenants.assigned_agent_id IS 'Foreign key to agents table - the AI agent assigned to this tenant';
