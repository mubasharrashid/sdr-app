"""
KnowledgeBase Repository - Database operations for knowledge_bases table.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from supabase import Client

from app.schemas.knowledge_base import KnowledgeBaseCreateInternal, KnowledgeBaseUpdate


class KnowledgeBaseRepository:
    """Repository for knowledge base database operations."""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.table = supabase.table("knowledge_bases")
    
    async def create(self, kb: KnowledgeBaseCreateInternal) -> Dict[str, Any]:
        """Create a new knowledge base."""
        data = kb.model_dump(exclude_unset=True)
        result = self.table.insert(data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, kb_id: UUID) -> Optional[Dict[str, Any]]:
        """Get knowledge base by ID."""
        result = self.table.select("*").eq("id", str(kb_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_by_tenant(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        kb_type: Optional[str] = None,
        agent_id: Optional[UUID] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get all knowledge bases for a tenant."""
        query = self.table.select("*", count="exact").eq("tenant_id", str(tenant_id))
        
        if status:
            query = query.eq("status", status)
        if kb_type:
            query = query.eq("kb_type", kb_type)
        if agent_id:
            query = query.eq("agent_id", str(agent_id))
        
        query = query.order("created_at", desc=True)
        query = query.range(skip, skip + limit - 1)
        
        result = query.execute()
        total = result.count if result.count else 0
        
        return result.data, total
    
    async def get_by_agent(self, agent_id: UUID, tenant_id: UUID) -> List[Dict[str, Any]]:
        """Get knowledge bases for a specific agent."""
        result = (
            self.table.select("*")
            .eq("tenant_id", str(tenant_id))
            .eq("agent_id", str(agent_id))
            .eq("status", "active")
            .execute()
        )
        return result.data
    
    async def update(self, kb_id: UUID, kb: KnowledgeBaseUpdate) -> Optional[Dict[str, Any]]:
        """Update a knowledge base."""
        data = kb.model_dump(exclude_unset=True, exclude_none=True)
        if not data:
            return await self.get_by_id(kb_id)
        
        result = self.table.update(data).eq("id", str(kb_id)).execute()
        return result.data[0] if result.data else None
    
    async def update_stats(
        self, 
        kb_id: UUID, 
        document_count: int, 
        total_chunks: int
    ) -> Optional[Dict[str, Any]]:
        """Update knowledge base statistics."""
        from datetime import datetime, timezone
        data = {
            "document_count": document_count,
            "total_chunks": total_chunks,
            "last_synced_at": datetime.now(timezone.utc).isoformat(),
        }
        result = self.table.update(data).eq("id", str(kb_id)).execute()
        return result.data[0] if result.data else None
    
    async def delete(self, kb_id: UUID) -> bool:
        """Delete a knowledge base."""
        result = self.table.delete().eq("id", str(kb_id)).execute()
        return len(result.data) > 0
    
    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count knowledge bases for a tenant."""
        result = self.table.select("*", count="exact").eq("tenant_id", str(tenant_id)).execute()
        return result.count if result.count else 0
