"""
TenantAgent Repository - Database operations for tenant_agents table.

Uses Supabase REST API for CRUD operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from supabase import Client
from datetime import datetime, timezone

from app.schemas.tenant_agent import TenantAgentCreateInternal, TenantAgentUpdate


class TenantAgentRepository:
    """Repository for tenant_agent database operations."""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.table = supabase.table("tenant_agents")
    
    async def create(self, tenant_agent: TenantAgentCreateInternal) -> Dict[str, Any]:
        """Create a new tenant-agent assignment."""
        data = tenant_agent.model_dump(exclude_unset=True)
        result = self.table.insert(data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, tenant_agent_id: UUID) -> Optional[Dict[str, Any]]:
        """Get tenant_agent by ID."""
        result = self.table.select("*").eq("id", str(tenant_agent_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_by_tenant_and_agent(
        self, 
        tenant_id: UUID, 
        agent_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get tenant_agent by tenant and agent IDs."""
        result = (
            self.table.select("*")
            .eq("tenant_id", str(tenant_id))
            .eq("agent_id", str(agent_id))
            .execute()
        )
        return result.data[0] if result.data else None
    
    async def get_active_for_tenant(self, tenant_id: UUID) -> Optional[Dict[str, Any]]:
        """Get the active agent assignment for a tenant."""
        result = (
            self.table.select("*")
            .eq("tenant_id", str(tenant_id))
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else None
    
    async def get_all_for_tenant(
        self,
        tenant_id: UUID,
        active_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get all agent assignments for a tenant."""
        query = self.table.select("*").eq("tenant_id", str(tenant_id))
        if active_only:
            query = query.eq("is_active", True)
        query = query.order("created_at", desc=True)
        result = query.execute()
        return result.data
    
    async def get_all_for_agent(
        self,
        agent_id: UUID,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """Get all tenant assignments for an agent."""
        query = self.table.select("*").eq("agent_id", str(agent_id))
        if active_only:
            query = query.eq("is_active", True)
        result = query.execute()
        return result.data
    
    async def update(
        self, 
        tenant_agent_id: UUID, 
        tenant_agent: TenantAgentUpdate
    ) -> Optional[Dict[str, Any]]:
        """Update a tenant_agent assignment."""
        data = tenant_agent.model_dump(exclude_unset=True, exclude_none=True)
        if not data:
            return await self.get_by_id(tenant_agent_id)
        
        result = self.table.update(data).eq("id", str(tenant_agent_id)).execute()
        return result.data[0] if result.data else None
    
    async def activate(self, tenant_agent_id: UUID) -> Optional[Dict[str, Any]]:
        """Activate a tenant_agent assignment."""
        data = {
            "is_active": True,
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "deactivated_at": None,
        }
        result = self.table.update(data).eq("id", str(tenant_agent_id)).execute()
        return result.data[0] if result.data else None
    
    async def deactivate(self, tenant_agent_id: UUID) -> Optional[Dict[str, Any]]:
        """Deactivate a tenant_agent assignment."""
        data = {
            "is_active": False,
            "deactivated_at": datetime.now(timezone.utc).isoformat(),
        }
        result = self.table.update(data).eq("id", str(tenant_agent_id)).execute()
        return result.data[0] if result.data else None
    
    async def deactivate_all_for_tenant(self, tenant_id: UUID) -> int:
        """Deactivate all agents for a tenant."""
        data = {
            "is_active": False,
            "deactivated_at": datetime.now(timezone.utc).isoformat(),
        }
        result = (
            self.table.update(data)
            .eq("tenant_id", str(tenant_id))
            .eq("is_active", True)
            .execute()
        )
        return len(result.data)
    
    async def delete(self, tenant_agent_id: UUID) -> bool:
        """Delete a tenant_agent assignment."""
        result = self.table.delete().eq("id", str(tenant_agent_id)).execute()
        return len(result.data) > 0
    
    async def exists(self, tenant_id: UUID, agent_id: UUID) -> bool:
        """Check if a tenant-agent assignment exists."""
        result = (
            self.table.select("id")
            .eq("tenant_id", str(tenant_id))
            .eq("agent_id", str(agent_id))
            .execute()
        )
        return len(result.data) > 0
    
    async def has_active_agent(self, tenant_id: UUID) -> bool:
        """Check if tenant has an active agent."""
        result = (
            self.table.select("id")
            .eq("tenant_id", str(tenant_id))
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        return len(result.data) > 0
    
    async def count_by_agent(self, agent_id: UUID, active_only: bool = True) -> int:
        """Count tenants using an agent."""
        query = self.table.select("*", count="exact").eq("agent_id", str(agent_id))
        if active_only:
            query = query.eq("is_active", True)
        result = query.execute()
        return result.count if result.count else 0
    
    async def increment_executions(self, tenant_agent_id: UUID) -> Optional[Dict[str, Any]]:
        """Increment execution count and update last execution time."""
        # First get current count
        current = await self.get_by_id(tenant_agent_id)
        if not current:
            return None
        
        data = {
            "total_executions": (current.get("total_executions") or 0) + 1,
            "last_execution_at": datetime.now(timezone.utc).isoformat(),
        }
        result = self.table.update(data).eq("id", str(tenant_agent_id)).execute()
        return result.data[0] if result.data else None
