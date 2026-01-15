"""Repository for Meeting CRUD operations."""
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timezone

from app.schemas.meeting import MeetingCreateInternal, MeetingUpdate, MeetingComplete


class MeetingRepository:
    """Repository for Meeting operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "meetings"
    
    async def create(self, data: MeetingCreateInternal) -> dict:
        """Create a new meeting."""
        insert_data = data.model_dump(exclude_none=True)
        
        uuid_fields = ["tenant_id", "lead_id", "campaign_id", "booked_by"]
        for field in uuid_fields:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = str(insert_data[field])
        
        if "scheduled_at" in insert_data:
            insert_data["scheduled_at"] = insert_data["scheduled_at"].isoformat()
        
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, meeting_id: UUID) -> Optional[dict]:
        """Get meeting by ID."""
        result = self.client.table(self.table).select("*").eq("id", str(meeting_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_by_lead(self, lead_id: UUID) -> List[dict]:
        """Get all meetings for a lead."""
        result = self.client.table(self.table).select("*")\
            .eq("lead_id", str(lead_id)).order("scheduled_at", desc=True).execute()
        return result.data
    
    async def get_by_tenant(
        self, tenant_id: UUID, status: Optional[str] = None,
        skip: int = 0, limit: int = 50
    ) -> Tuple[List[dict], int]:
        """Get all meetings for a tenant."""
        query = self.client.table(self.table).select("*", count="exact").eq("tenant_id", str(tenant_id))
        if status:
            query = query.eq("status", status)
        result = query.order("scheduled_at", desc=True).range(skip, skip + limit - 1).execute()
        return result.data, result.count or 0
    
    async def get_upcoming(self, tenant_id: UUID, limit: int = 20) -> List[dict]:
        """Get upcoming meetings."""
        now = datetime.now(timezone.utc).isoformat()
        result = self.client.table(self.table).select("*")\
            .eq("tenant_id", str(tenant_id))\
            .in_("status", ["scheduled", "confirmed"])\
            .gte("scheduled_at", now)\
            .order("scheduled_at").limit(limit).execute()
        return result.data
    
    async def update(self, meeting_id: UUID, data: MeetingUpdate) -> Optional[dict]:
        """Update a meeting."""
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(meeting_id)
        
        if "scheduled_at" in update_data and update_data["scheduled_at"]:
            update_data["scheduled_at"] = update_data["scheduled_at"].isoformat()
        
        result = self.client.table(self.table).update(update_data).eq("id", str(meeting_id)).execute()
        return result.data[0] if result.data else None
    
    async def confirm(self, meeting_id: UUID) -> Optional[dict]:
        """Confirm a meeting."""
        update_data = {
            "status": "confirmed",
            "confirmed_at": datetime.now(timezone.utc).isoformat()
        }
        result = self.client.table(self.table).update(update_data).eq("id", str(meeting_id)).execute()
        return result.data[0] if result.data else None
    
    async def complete(self, meeting_id: UUID, data: MeetingComplete) -> Optional[dict]:
        """Complete a meeting with notes."""
        update_data = data.model_dump(exclude_none=True)
        update_data["status"] = "completed"
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        if "follow_up_date" in update_data and update_data["follow_up_date"]:
            update_data["follow_up_date"] = str(update_data["follow_up_date"])
        
        result = self.client.table(self.table).update(update_data).eq("id", str(meeting_id)).execute()
        return result.data[0] if result.data else None
    
    async def cancel(self, meeting_id: UUID) -> Optional[dict]:
        """Cancel a meeting."""
        update_data = {
            "status": "cancelled",
            "cancelled_at": datetime.now(timezone.utc).isoformat()
        }
        result = self.client.table(self.table).update(update_data).eq("id", str(meeting_id)).execute()
        return result.data[0] if result.data else None
    
    async def reschedule(self, meeting_id: UUID, new_time: datetime) -> Optional[dict]:
        """Reschedule a meeting."""
        update_data = {
            "status": "rescheduled",
            "scheduled_at": new_time.isoformat()
        }
        result = self.client.table(self.table).update(update_data).eq("id", str(meeting_id)).execute()
        return result.data[0] if result.data else None
    
    async def delete(self, meeting_id: UUID) -> bool:
        """Delete a meeting."""
        result = self.client.table(self.table).delete().eq("id", str(meeting_id)).execute()
        return len(result.data) > 0 if result.data else False
    
    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count meetings for a tenant."""
        result = self.client.table(self.table).select("id", count="exact").eq("tenant_id", str(tenant_id)).execute()
        return result.count or 0
    
    async def count_upcoming(self, tenant_id: UUID) -> int:
        """Count upcoming meetings."""
        now = datetime.now(timezone.utc).isoformat()
        result = self.client.table(self.table).select("id", count="exact")\
            .eq("tenant_id", str(tenant_id))\
            .in_("status", ["scheduled", "confirmed"])\
            .gte("scheduled_at", now).execute()
        return result.count or 0
