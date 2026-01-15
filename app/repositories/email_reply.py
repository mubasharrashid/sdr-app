"""Repository for EmailReply CRUD operations."""
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timezone

from app.schemas.email_reply import EmailReplyCreateInternal, EmailReplyUpdate


class EmailReplyRepository:
    """Repository for EmailReply operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "email_replies"
    
    async def create(self, data: EmailReplyCreateInternal) -> dict:
        """Create a new email reply."""
        insert_data = data.model_dump(exclude_none=True)
        
        uuid_fields = ["tenant_id", "lead_id", "campaign_id", "sequence_step_id"]
        for field in uuid_fields:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = str(insert_data[field])
        
        if "received_at" in insert_data:
            insert_data["received_at"] = insert_data["received_at"].isoformat()
        
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, reply_id: UUID) -> Optional[dict]:
        """Get email reply by ID."""
        result = self.client.table(self.table).select("*").eq("id", str(reply_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_by_lead(self, lead_id: UUID) -> List[dict]:
        """Get all email replies for a lead."""
        result = self.client.table(self.table).select("*")\
            .eq("lead_id", str(lead_id)).order("received_at", desc=True).execute()
        return result.data
    
    async def get_by_tenant(
        self, tenant_id: UUID, requires_action: Optional[bool] = None,
        skip: int = 0, limit: int = 50
    ) -> Tuple[List[dict], int]:
        """Get all email replies for a tenant."""
        query = self.client.table(self.table).select("*", count="exact").eq("tenant_id", str(tenant_id))
        if requires_action is not None:
            query = query.eq("requires_action", requires_action)
        result = query.order("received_at", desc=True).range(skip, skip + limit - 1).execute()
        return result.data, result.count or 0
    
    async def get_requiring_action(self, tenant_id: UUID) -> List[dict]:
        """Get replies that need action."""
        result = self.client.table(self.table).select("*")\
            .eq("tenant_id", str(tenant_id)).eq("requires_action", True)\
            .eq("is_auto_reply", False).eq("is_out_of_office", False)\
            .order("received_at", desc=True).execute()
        return result.data
    
    async def update(self, reply_id: UUID, data: EmailReplyUpdate) -> Optional[dict]:
        """Update an email reply."""
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(reply_id)
        
        result = self.client.table(self.table).update(update_data).eq("id", str(reply_id)).execute()
        return result.data[0] if result.data else None
    
    async def mark_processed(self, reply_id: UUID) -> Optional[dict]:
        """Mark reply as processed."""
        update_data = {"processed_at": datetime.now(timezone.utc).isoformat()}
        result = self.client.table(self.table).update(update_data).eq("id", str(reply_id)).execute()
        return result.data[0] if result.data else None
    
    async def mark_action_taken(
        self, reply_id: UUID, action: str, user_id: UUID
    ) -> Optional[dict]:
        """Mark action taken on reply."""
        update_data = {
            "requires_action": False,
            "action_taken": action,
            "action_taken_at": datetime.now(timezone.utc).isoformat(),
            "action_taken_by": str(user_id)
        }
        result = self.client.table(self.table).update(update_data).eq("id", str(reply_id)).execute()
        return result.data[0] if result.data else None
    
    async def delete(self, reply_id: UUID) -> bool:
        """Delete an email reply."""
        result = self.client.table(self.table).delete().eq("id", str(reply_id)).execute()
        return len(result.data) > 0 if result.data else False
    
    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count email replies for a tenant."""
        result = self.client.table(self.table).select("id", count="exact").eq("tenant_id", str(tenant_id)).execute()
        return result.count or 0
    
    async def count_requiring_action(self, tenant_id: UUID) -> int:
        """Count replies requiring action."""
        result = self.client.table(self.table).select("id", count="exact")\
            .eq("tenant_id", str(tenant_id)).eq("requires_action", True).execute()
        return result.count or 0
