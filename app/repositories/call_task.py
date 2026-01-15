"""Repository for CallTask CRUD operations."""
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timezone

from app.schemas.call_task import CallTaskCreateInternal, CallTaskUpdate, CallTaskComplete


class CallTaskRepository:
    """Repository for CallTask operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "call_tasks"
    
    async def create(self, data: CallTaskCreateInternal) -> dict:
        """Create a new call task."""
        insert_data = data.model_dump(exclude_none=True)
        
        uuid_fields = ["tenant_id", "lead_id", "campaign_id", "agent_id", "created_by"]
        for field in uuid_fields:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = str(insert_data[field])
        
        if "scheduled_at" in insert_data and insert_data["scheduled_at"]:
            insert_data["scheduled_at"] = insert_data["scheduled_at"].isoformat()
        
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, task_id: UUID) -> Optional[dict]:
        """Get call task by ID."""
        result = self.client.table(self.table).select("*").eq("id", str(task_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_by_lead(self, lead_id: UUID) -> List[dict]:
        """Get all call tasks for a lead."""
        result = self.client.table(self.table).select("*")\
            .eq("lead_id", str(lead_id)).order("created_at", desc=True).execute()
        return result.data
    
    async def get_by_tenant(
        self, tenant_id: UUID, status: Optional[str] = None,
        skip: int = 0, limit: int = 50
    ) -> Tuple[List[dict], int]:
        """Get all call tasks for a tenant."""
        query = self.client.table(self.table).select("*", count="exact").eq("tenant_id", str(tenant_id))
        if status:
            query = query.eq("status", status)
        result = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        return result.data, result.count or 0
    
    async def get_scheduled(self, tenant_id: Optional[UUID] = None) -> List[dict]:
        """Get scheduled call tasks."""
        query = self.client.table(self.table).select("*").eq("status", "scheduled")
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        result = query.order("scheduled_at").execute()
        return result.data
    
    async def update(self, task_id: UUID, data: CallTaskUpdate) -> Optional[dict]:
        """Update a call task."""
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(task_id)
        
        if "scheduled_at" in update_data and update_data["scheduled_at"]:
            update_data["scheduled_at"] = update_data["scheduled_at"].isoformat()
        
        result = self.client.table(self.table).update(update_data).eq("id", str(task_id)).execute()
        return result.data[0] if result.data else None
    
    async def start(self, task_id: UUID, retell_call_id: Optional[str] = None) -> Optional[dict]:
        """Start a call."""
        update_data = {
            "status": "in_progress",
            "call_started_at": datetime.now(timezone.utc).isoformat()
        }
        if retell_call_id:
            update_data["retell_call_id"] = retell_call_id
        result = self.client.table(self.table).update(update_data).eq("id", str(task_id)).execute()
        return result.data[0] if result.data else None
    
    async def complete(self, task_id: UUID, data: CallTaskComplete) -> Optional[dict]:
        """Complete a call with results."""
        update_data = data.model_dump(exclude_none=True)
        update_data["status"] = "completed"
        update_data["call_ended_at"] = datetime.now(timezone.utc).isoformat()
        
        result = self.client.table(self.table).update(update_data).eq("id", str(task_id)).execute()
        return result.data[0] if result.data else None
    
    async def fail(self, task_id: UUID, status: str = "failed") -> Optional[dict]:
        """Mark call as failed."""
        update_data = {
            "status": status,
            "call_ended_at": datetime.now(timezone.utc).isoformat()
        }
        result = self.client.table(self.table).update(update_data).eq("id", str(task_id)).execute()
        return result.data[0] if result.data else None
    
    async def delete(self, task_id: UUID) -> bool:
        """Delete a call task."""
        result = self.client.table(self.table).delete().eq("id", str(task_id)).execute()
        return len(result.data) > 0 if result.data else False
    
    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count call tasks for a tenant."""
        result = self.client.table(self.table).select("id", count="exact").eq("tenant_id", str(tenant_id)).execute()
        return result.count or 0
