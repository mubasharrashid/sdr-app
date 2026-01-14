"""Repository for Workflow CRUD operations."""
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timezone

from app.schemas.workflow import (
    WorkflowCreateInternal,
    WorkflowUpdate,
    WorkflowUpdateExecution
)


class WorkflowRepository:
    """Repository for Workflow operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "workflows"
    
    async def create(self, data: WorkflowCreateInternal) -> dict:
        """Create a new workflow."""
        insert_data = data.model_dump(exclude_none=True)
        
        # Convert UUIDs to strings
        for field in ["tenant_id", "agent_id", "created_by"]:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = str(insert_data[field])
        
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, workflow_id: UUID) -> Optional[dict]:
        """Get workflow by ID."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("id", str(workflow_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def get_by_tenant(
        self, 
        tenant_id: UUID,
        status: Optional[str] = None,
        workflow_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[dict], int]:
        """Get all workflows for a tenant."""
        query = self.client.table(self.table)\
            .select("*", count="exact")\
            .eq("tenant_id", str(tenant_id))
        
        if status:
            query = query.eq("status", status)
        if workflow_type:
            query = query.eq("workflow_type", workflow_type)
        
        result = query.order("created_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()
        return result.data, result.count or 0
    
    async def get_by_agent(
        self, 
        agent_id: UUID,
        tenant_id: Optional[UUID] = None
    ) -> List[dict]:
        """Get workflows for an agent."""
        query = self.client.table(self.table)\
            .select("*")\
            .eq("agent_id", str(agent_id))
        
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        
        result = query.order("name").execute()
        return result.data
    
    async def get_by_trigger(
        self, 
        trigger_event: str,
        tenant_id: Optional[UUID] = None
    ) -> List[dict]:
        """Get active workflows by trigger event."""
        query = self.client.table(self.table)\
            .select("*")\
            .eq("trigger_event", trigger_event)\
            .eq("status", "active")\
            .eq("is_enabled", True)
        
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        
        result = query.execute()
        return result.data
    
    async def get_scheduled(self) -> List[dict]:
        """Get all active scheduled workflows."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("workflow_type", "scheduled")\
            .eq("status", "active")\
            .eq("is_enabled", True)\
            .execute()
        return result.data
    
    async def update(
        self, 
        workflow_id: UUID, 
        data: WorkflowUpdate
    ) -> Optional[dict]:
        """Update a workflow."""
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(workflow_id)
        
        # Convert UUID fields
        if "agent_id" in update_data and update_data["agent_id"]:
            update_data["agent_id"] = str(update_data["agent_id"])
        
        # Convert datetime fields
        if "next_scheduled_at" in update_data and update_data["next_scheduled_at"]:
            update_data["next_scheduled_at"] = update_data["next_scheduled_at"].isoformat()
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(workflow_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def activate(self, workflow_id: UUID) -> Optional[dict]:
        """Activate a workflow."""
        result = self.client.table(self.table)\
            .update({"status": "active", "is_enabled": True})\
            .eq("id", str(workflow_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def pause(self, workflow_id: UUID) -> Optional[dict]:
        """Pause a workflow."""
        result = self.client.table(self.table)\
            .update({"status": "paused"})\
            .eq("id", str(workflow_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def archive(self, workflow_id: UUID) -> Optional[dict]:
        """Archive a workflow."""
        result = self.client.table(self.table)\
            .update({"status": "archived", "is_enabled": False})\
            .eq("id", str(workflow_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def record_execution(
        self,
        workflow_id: UUID,
        success: bool,
        error: Optional[str] = None
    ) -> Optional[dict]:
        """Record workflow execution result."""
        # Get current stats
        current = await self.get_by_id(workflow_id)
        if not current:
            return None
        
        update_data = {
            "total_executions": (current.get("total_executions") or 0) + 1,
            "last_executed_at": datetime.now(timezone.utc).isoformat()
        }
        
        if success:
            update_data["successful_executions"] = (current.get("successful_executions") or 0) + 1
            update_data["last_error"] = None
        else:
            update_data["failed_executions"] = (current.get("failed_executions") or 0) + 1
            update_data["last_error"] = error
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(workflow_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def delete(self, workflow_id: UUID) -> bool:
        """Delete a workflow."""
        result = self.client.table(self.table)\
            .delete()\
            .eq("id", str(workflow_id))\
            .execute()
        return len(result.data) > 0 if result.data else False
    
    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count workflows for a tenant."""
        result = self.client.table(self.table)\
            .select("id", count="exact")\
            .eq("tenant_id", str(tenant_id))\
            .execute()
        return result.count or 0
    
    async def count_active_by_tenant(self, tenant_id: UUID) -> int:
        """Count active workflows for a tenant."""
        result = self.client.table(self.table)\
            .select("id", count="exact")\
            .eq("tenant_id", str(tenant_id))\
            .eq("status", "active")\
            .execute()
        return result.count or 0
