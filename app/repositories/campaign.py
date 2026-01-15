"""Repository for Campaign CRUD operations."""
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timezone

from app.schemas.campaign import (
    CampaignCreateInternal,
    CampaignUpdate,
    CampaignUpdateMetrics
)


class CampaignRepository:
    """Repository for Campaign operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "campaigns"
    
    async def create(self, data: CampaignCreateInternal) -> dict:
        """Create a new campaign."""
        insert_data = data.model_dump(exclude_none=True)
        
        # Convert UUIDs to strings
        uuid_fields = ["tenant_id", "agent_id", "created_by"]
        for field in uuid_fields:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = str(insert_data[field])
        
        # Convert datetime fields
        for field in ["scheduled_start_at", "scheduled_end_at"]:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = insert_data[field].isoformat()
        
        # Convert time fields to string
        for field in ["sending_start_time", "sending_end_time"]:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = str(insert_data[field])
        
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, campaign_id: UUID) -> Optional[dict]:
        """Get campaign by ID."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("id", str(campaign_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def get_by_tenant(
        self, 
        tenant_id: UUID,
        status: Optional[str] = None,
        campaign_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[dict], int]:
        """Get all campaigns for a tenant."""
        query = self.client.table(self.table)\
            .select("*", count="exact")\
            .eq("tenant_id", str(tenant_id))
        
        if status:
            query = query.eq("status", status)
        if campaign_type:
            query = query.eq("campaign_type", campaign_type)
        
        result = query.order("created_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()
        return result.data, result.count or 0
    
    async def get_active(self, tenant_id: Optional[UUID] = None) -> List[dict]:
        """Get all active campaigns."""
        query = self.client.table(self.table)\
            .select("*")\
            .eq("status", "active")
        
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        
        result = query.order("created_at", desc=True).execute()
        return result.data
    
    async def get_by_agent(
        self, 
        agent_id: UUID,
        tenant_id: Optional[UUID] = None
    ) -> List[dict]:
        """Get campaigns for an agent."""
        query = self.client.table(self.table)\
            .select("*")\
            .eq("agent_id", str(agent_id))
        
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        
        result = query.order("created_at", desc=True).execute()
        return result.data
    
    async def update(
        self, 
        campaign_id: UUID, 
        data: CampaignUpdate
    ) -> Optional[dict]:
        """Update a campaign."""
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(campaign_id)
        
        # Convert UUID fields
        if "agent_id" in update_data and update_data["agent_id"]:
            update_data["agent_id"] = str(update_data["agent_id"])
        
        # Convert datetime fields
        for field in ["scheduled_start_at", "scheduled_end_at"]:
            if field in update_data and update_data[field]:
                update_data[field] = update_data[field].isoformat()
        
        # Convert time fields
        for field in ["sending_start_time", "sending_end_time"]:
            if field in update_data and update_data[field]:
                update_data[field] = str(update_data[field])
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(campaign_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def update_metrics(
        self, 
        campaign_id: UUID, 
        data: CampaignUpdateMetrics
    ) -> Optional[dict]:
        """Update campaign metrics."""
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(campaign_id)
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(campaign_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def start(self, campaign_id: UUID) -> Optional[dict]:
        """Start a campaign."""
        update_data = {
            "status": "active",
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(campaign_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def pause(self, campaign_id: UUID) -> Optional[dict]:
        """Pause a campaign."""
        result = self.client.table(self.table)\
            .update({"status": "paused"})\
            .eq("id", str(campaign_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def resume(self, campaign_id: UUID) -> Optional[dict]:
        """Resume a paused campaign."""
        result = self.client.table(self.table)\
            .update({"status": "active"})\
            .eq("id", str(campaign_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def complete(self, campaign_id: UUID) -> Optional[dict]:
        """Complete a campaign."""
        update_data = {
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(campaign_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def archive(self, campaign_id: UUID) -> Optional[dict]:
        """Archive a campaign."""
        result = self.client.table(self.table)\
            .update({"status": "archived"})\
            .eq("id", str(campaign_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def delete(self, campaign_id: UUID) -> bool:
        """Delete a campaign."""
        result = self.client.table(self.table)\
            .delete()\
            .eq("id", str(campaign_id))\
            .execute()
        return len(result.data) > 0 if result.data else False
    
    async def count_by_tenant(self, tenant_id: UUID) -> int:
        """Count campaigns for a tenant."""
        result = self.client.table(self.table)\
            .select("id", count="exact")\
            .eq("tenant_id", str(tenant_id))\
            .execute()
        return result.count or 0
    
    async def count_active(self, tenant_id: UUID) -> int:
        """Count active campaigns for a tenant."""
        result = self.client.table(self.table)\
            .select("id", count="exact")\
            .eq("tenant_id", str(tenant_id))\
            .eq("status", "active")\
            .execute()
        return result.count or 0
    
    async def increment_metric(
        self, 
        campaign_id: UUID, 
        metric: str, 
        amount: int = 1
    ) -> Optional[dict]:
        """Increment a specific metric."""
        current = await self.get_by_id(campaign_id)
        if not current:
            return None
        
        current_value = current.get(metric, 0) or 0
        update_data = {metric: current_value + amount}
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(campaign_id))\
            .execute()
        return result.data[0] if result.data else None
