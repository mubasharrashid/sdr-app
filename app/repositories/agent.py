"""
Agent Repository - Database operations for agents table.

Uses Supabase REST API for CRUD operations.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from supabase import Client

from app.schemas.agent import AgentCreate, AgentUpdate


class AgentRepository:
    """Repository for agent database operations."""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.table = supabase.table("agents")
    
    async def create(self, agent: AgentCreate) -> Dict[str, Any]:
        """Create a new agent."""
        data = agent.model_dump(exclude_unset=True)
        result = self.table.insert(data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, agent_id: UUID) -> Optional[Dict[str, Any]]:
        """Get agent by ID."""
        result = self.table.select("*").eq("id", str(agent_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get agent by slug."""
        result = self.table.select("*").eq("slug", slug).execute()
        return result.data[0] if result.data else None
    
    async def get_all(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all agents."""
        query = self.table.select("*")
        if active_only:
            query = query.eq("is_active", True)
        query = query.order("slug")
        result = query.execute()
        return result.data
    
    async def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get agents by category."""
        result = self.table.select("*").eq("category", category).execute()
        return result.data
    
    async def update(self, agent_id: UUID, agent: AgentUpdate) -> Optional[Dict[str, Any]]:
        """Update an agent."""
        data = agent.model_dump(exclude_unset=True, exclude_none=True)
        if not data:
            return await self.get_by_id(agent_id)
        
        result = self.table.update(data).eq("id", str(agent_id)).execute()
        return result.data[0] if result.data else None
    
    async def delete(self, agent_id: UUID) -> bool:
        """Delete an agent."""
        result = self.table.delete().eq("id", str(agent_id)).execute()
        return len(result.data) > 0
    
    async def exists_by_slug(self, slug: str, exclude_id: Optional[UUID] = None) -> bool:
        """Check if an agent with the given slug exists."""
        query = self.table.select("id").eq("slug", slug)
        if exclude_id:
            query = query.neq("id", str(exclude_id))
        result = query.execute()
        return len(result.data) > 0
    
    async def count_active(self) -> int:
        """Count active agents."""
        result = self.table.select("*", count="exact").eq("is_active", True).execute()
        return result.count if result.count else 0
