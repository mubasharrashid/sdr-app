"""Repository for Email Template CRUD operations."""
from typing import Optional, List, Tuple
from uuid import UUID

from app.schemas.email_template import (
    EmailTemplateCreateInternal,
    EmailTemplateUpdate
)


class EmailTemplateRepository:
    """Repository for Email Template operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "email_templates"
    
    async def create(self, data: EmailTemplateCreateInternal) -> dict:
        """Create a new email template."""
        insert_data = data.model_dump(exclude_none=True)
        
        # Convert UUIDs to strings
        uuid_fields = ["tenant_id", "icp_person_id", "created_by"]
        for field in uuid_fields:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = str(insert_data[field])
        
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, template_id: UUID) -> Optional[dict]:
        """Get email template by ID."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("id", str(template_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def get_by_tenant(
        self, 
        tenant_id: UUID, 
        icp_person_id: Optional[UUID] = None,
        template_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0, 
        limit: int = 50
    ) -> Tuple[List[dict], int]:
        """Get all email templates for a tenant with optional filters."""
        query = self.client.table(self.table).select("*", count="exact").eq("tenant_id", str(tenant_id))
        
        if icp_person_id:
            query = query.eq("icp_person_id", str(icp_person_id))
        
        if template_type:
            query = query.eq("template_type", template_type)
        
        if is_active is not None:
            query = query.eq("is_active", is_active)
        
        result = query.order("email_sequence", desc=False).order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        return result.data, result.count or 0
    
    async def get_by_icp_and_sequence(
        self, 
        tenant_id: UUID, 
        icp_person_id: UUID, 
        email_sequence: int
    ) -> Optional[dict]:
        """Get email template by ICP person and sequence number."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("tenant_id", str(tenant_id))\
            .eq("icp_person_id", str(icp_person_id))\
            .eq("email_sequence", email_sequence)\
            .eq("is_active", True)\
            .execute()
        return result.data[0] if result.data else None
    
    async def update(self, template_id: UUID, data: EmailTemplateUpdate) -> Optional[dict]:
        """Update an email template."""
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(template_id)
        
        # Convert UUIDs to strings
        if "icp_person_id" in update_data and update_data["icp_person_id"]:
            update_data["icp_person_id"] = str(update_data["icp_person_id"])
        
        result = self.client.table(self.table).update(update_data).eq("id", str(template_id)).execute()
        return result.data[0] if result.data else None
    
    async def delete(self, template_id: UUID) -> bool:
        """Delete an email template."""
        result = self.client.table(self.table).delete().eq("id", str(template_id)).execute()
        return len(result.data) > 0 if result.data else False
    
    async def increment_usage(self, template_id: UUID) -> Optional[dict]:
        """Increment usage counter for a template."""
        from datetime import datetime, timezone
        result = self.client.table(self.table)\
            .update({
                "times_used": self.client.rpc("increment", {"table": self.table, "column": "times_used", "id": str(template_id)}),
                "last_used_at": datetime.now(timezone.utc).isoformat()
            })\
            .eq("id", str(template_id))\
            .execute()
        
        # Fallback: get current value and increment manually
        current = await self.get_by_id(template_id)
        if current:
            times_used = (current.get("times_used") or 0) + 1
            result = self.client.table(self.table)\
                .update({
                    "times_used": times_used,
                    "last_used_at": datetime.now(timezone.utc).isoformat()
                })\
                .eq("id", str(template_id))\
                .execute()
            return result.data[0] if result.data else None
        return None
