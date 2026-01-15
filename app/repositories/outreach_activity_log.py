"""Repository for OutreachActivityLog CRUD operations."""
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timezone

from app.schemas.outreach_activity_log import OutreachActivityLogCreateInternal


class OutreachActivityLogRepository:
    """Repository for OutreachActivityLog operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "outreach_activity_logs"
    
    async def create(self, data: OutreachActivityLogCreateInternal) -> dict:
        """Create a new activity log."""
        insert_data = data.model_dump(exclude_none=True)
        
        uuid_fields = ["tenant_id", "lead_id", "campaign_id", "sequence_step_id", 
                       "related_id", "source_user_id"]
        for field in uuid_fields:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = str(insert_data[field])
        
        for field in ["activity_at", "link_clicked_at"]:
            if field in insert_data and insert_data[field]:
                insert_data[field] = insert_data[field].isoformat()
        
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, log_id: UUID) -> Optional[dict]:
        """Get activity log by ID."""
        result = self.client.table(self.table).select("*").eq("id", str(log_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_by_lead(
        self, lead_id: UUID, activity_type: Optional[str] = None,
        skip: int = 0, limit: int = 100
    ) -> Tuple[List[dict], int]:
        """Get activity timeline for a lead."""
        query = self.client.table(self.table).select("*", count="exact").eq("lead_id", str(lead_id))
        if activity_type:
            query = query.eq("activity_type", activity_type)
        result = query.order("activity_at", desc=True).range(skip, skip + limit - 1).execute()
        return result.data, result.count or 0
    
    async def get_by_campaign(
        self, campaign_id: UUID, activity_type: Optional[str] = None,
        skip: int = 0, limit: int = 100
    ) -> Tuple[List[dict], int]:
        """Get activities for a campaign."""
        query = self.client.table(self.table).select("*", count="exact").eq("campaign_id", str(campaign_id))
        if activity_type:
            query = query.eq("activity_type", activity_type)
        result = query.order("activity_at", desc=True).range(skip, skip + limit - 1).execute()
        return result.data, result.count or 0
    
    async def get_by_tenant(
        self, tenant_id: UUID, channel: Optional[str] = None,
        skip: int = 0, limit: int = 100
    ) -> Tuple[List[dict], int]:
        """Get all activities for a tenant."""
        query = self.client.table(self.table).select("*", count="exact").eq("tenant_id", str(tenant_id))
        if channel:
            query = query.eq("channel", channel)
        result = query.order("activity_at", desc=True).range(skip, skip + limit - 1).execute()
        return result.data, result.count or 0
    
    async def get_positive_engagements(self, lead_id: UUID) -> List[dict]:
        """Get positive engagement activities for a lead."""
        positive_types = ["email_replied", "email_clicked", "call_connected", 
                        "meeting_booked", "linkedin_reply"]
        result = self.client.table(self.table).select("*")\
            .eq("lead_id", str(lead_id)).in_("activity_type", positive_types)\
            .order("activity_at", desc=True).execute()
        return result.data
    
    async def count_by_type(self, lead_id: UUID, activity_type: str) -> int:
        """Count activities of a specific type for a lead."""
        result = self.client.table(self.table).select("id", count="exact")\
            .eq("lead_id", str(lead_id)).eq("activity_type", activity_type).execute()
        return result.count or 0
    
    async def count_by_campaign(self, campaign_id: UUID, activity_type: Optional[str] = None) -> int:
        """Count activities for a campaign."""
        query = self.client.table(self.table).select("id", count="exact").eq("campaign_id", str(campaign_id))
        if activity_type:
            query = query.eq("activity_type", activity_type)
        result = query.execute()
        return result.count or 0
    
    # Note: Activity logs are typically immutable - no update/delete methods


# Helper function for logging activities
async def log_activity(
    client,
    tenant_id: UUID,
    lead_id: UUID,
    activity_type: str,
    channel: Optional[str] = None,
    description: Optional[str] = None,
    campaign_id: Optional[UUID] = None,
    metadata: Optional[dict] = None,
    source: str = "system"
) -> dict:
    """Convenience function to log an activity."""
    repo = OutreachActivityLogRepository(client)
    
    data = OutreachActivityLogCreateInternal(
        tenant_id=str(tenant_id),
        lead_id=str(lead_id),
        activity_type=activity_type,
        channel=channel,
        description=description,
        campaign_id=str(campaign_id) if campaign_id else None,
        metadata=metadata or {},
        source=source,
        activity_at=datetime.now(timezone.utc)
    )
    
    return await repo.create(data)
