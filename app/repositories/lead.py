"""Repository for Lead CRUD operations."""
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timezone

from app.schemas.lead import LeadCreateInternal, LeadUpdate


class LeadRepository:
    """Repository for Lead operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "leads"
    
    async def create(self, data: LeadCreateInternal) -> dict:
        """Create a new lead."""
        insert_data = data.model_dump(exclude_none=True)
        
        uuid_fields = ["tenant_id", "campaign_id", "assigned_to"]
        for field in uuid_fields:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = str(insert_data[field])
        
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, lead_id: UUID) -> Optional[dict]:
        """Get lead by ID."""
        result = self.client.table(self.table).select("*").eq("id", str(lead_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_by_email(self, tenant_id: UUID, email: str) -> Optional[dict]:
        """Get lead by email within a tenant."""
        result = self.client.table(self.table).select("*")\
            .eq("tenant_id", str(tenant_id)).eq("email", email).execute()
        return result.data[0] if result.data else None
    
    async def get_by_tenant(
        self, tenant_id: UUID, status: Optional[str] = None,
        campaign_id: Optional[UUID] = None, skip: int = 0, limit: int = 50,
        has_calls_made: Optional[bool] = None,
        has_emails_sent: Optional[bool] = None,
        has_emails_replied: Optional[bool] = None,
        has_meetings_booked: Optional[bool] = None,
        has_been_contacted: Optional[bool] = None,
        source: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[List[dict], int]:
        """Get all leads for a tenant with optional activity filters."""
        query = self.client.table(self.table).select("*", count="exact").eq("tenant_id", str(tenant_id))
        if status:
            query = query.eq("status", status)
        if campaign_id:
            query = query.eq("campaign_id", str(campaign_id))
        if source:
            query = query.eq("source", source)
        if start_date:
            query = query.gte("created_at", start_date.isoformat())
        if end_date:
            query = query.lte("created_at", end_date.isoformat())
        
        # Activity-based filters
        if has_calls_made is not None:
            if has_calls_made:
                query = query.gt("calls_made", 0)
            else:
                query = query.eq("calls_made", 0)
        
        if has_emails_sent is not None:
            if has_emails_sent:
                query = query.gt("emails_sent", 0)
            else:
                query = query.eq("emails_sent", 0)
        
        if has_emails_replied is not None:
            if has_emails_replied:
                query = query.gt("emails_replied", 0)
            else:
                query = query.eq("emails_replied", 0)
        
        if has_meetings_booked is not None:
            if has_meetings_booked:
                query = query.gt("meetings_booked", 0)
            else:
                query = query.eq("meetings_booked", 0)
        
        if has_been_contacted is not None:
            if has_been_contacted:
                # Contacted means either calls_made > 0 OR emails_sent > 0
                query = query.or_("calls_made.gt.0,emails_sent.gt.0")
            else:
                # Not contacted means both calls_made = 0 AND emails_sent = 0
                query = query.eq("calls_made", 0).eq("emails_sent", 0)
        
        result = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        return result.data, result.count or 0
    
    async def search(
        self, tenant_id: UUID, query: str, skip: int = 0, limit: int = 50
    ) -> Tuple[List[dict], int]:
        """Search leads by name, email, or company."""
        result = self.client.table(self.table).select("*", count="exact")\
            .eq("tenant_id", str(tenant_id))\
            .or_(f"email.ilike.%{query}%,full_name.ilike.%{query}%,company_name.ilike.%{query}%")\
            .order("lead_score", desc=True).range(skip, skip + limit - 1).execute()
        return result.data, result.count or 0
    
    async def update(self, lead_id: UUID, data: LeadUpdate) -> Optional[dict]:
        """Update a lead."""
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(lead_id)
        
        for field in ["campaign_id", "assigned_to"]:
            if field in update_data and update_data[field]:
                update_data[field] = str(update_data[field])
        
        result = self.client.table(self.table).update(update_data).eq("id", str(lead_id)).execute()
        return result.data[0] if result.data else None
    
    async def update_status(self, lead_id: UUID, status: str) -> Optional[dict]:
        """Update lead status."""
        result = self.client.table(self.table).update({"status": status}).eq("id", str(lead_id)).execute()
        return result.data[0] if result.data else None
    
    async def update_last_contacted(self, lead_id: UUID) -> Optional[dict]:
        """Update last contacted timestamp."""
        result = self.client.table(self.table)\
            .update({"last_contacted_at": datetime.now(timezone.utc).isoformat()})\
            .eq("id", str(lead_id)).execute()
        return result.data[0] if result.data else None
    
    async def increment_metric(self, lead_id: UUID, metric: str, amount: int = 1) -> Optional[dict]:
        """Increment a metric field."""
        current = await self.get_by_id(lead_id)
        if not current:
            return None
        current_value = current.get(metric, 0) or 0
        result = self.client.table(self.table)\
            .update({metric: current_value + amount}).eq("id", str(lead_id)).execute()
        return result.data[0] if result.data else None
    
    async def delete(self, lead_id: UUID) -> bool:
        """Delete a lead."""
        result = self.client.table(self.table).delete().eq("id", str(lead_id)).execute()
        return len(result.data) > 0 if result.data else False
    
    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count leads for a tenant."""
        result = self.client.table(self.table).select("id", count="exact").eq("tenant_id", str(tenant_id)).execute()
        return result.count or 0
    
    async def count_by_status(self, tenant_id: UUID, status: str) -> int:
        """Count leads by status."""
        result = self.client.table(self.table).select("id", count="exact")\
            .eq("tenant_id", str(tenant_id)).eq("status", status).execute()
        return result.count or 0
