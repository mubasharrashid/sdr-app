"""Repository for CampaignSequence CRUD operations."""
from typing import Optional, List, Tuple
from uuid import UUID

from app.schemas.campaign_sequence import (
    CampaignSequenceCreateInternal,
    CampaignSequenceUpdate,
    CampaignSequenceUpdateMetrics
)


class CampaignSequenceRepository:
    """Repository for CampaignSequence operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "campaign_sequences"
    
    async def create(self, data: CampaignSequenceCreateInternal) -> dict:
        """Create a new campaign sequence step."""
        insert_data = data.model_dump(exclude_none=True)
        
        # Convert UUIDs to strings
        uuid_fields = ["campaign_id", "tenant_id", "email_template_id", "ab_test_group_id"]
        for field in uuid_fields:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = str(insert_data[field])
        
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, sequence_id: UUID) -> Optional[dict]:
        """Get sequence step by ID."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("id", str(sequence_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def get_by_campaign(
        self, 
        campaign_id: UUID,
        active_only: bool = False
    ) -> List[dict]:
        """Get all sequence steps for a campaign, ordered by step_number."""
        query = self.client.table(self.table)\
            .select("*")\
            .eq("campaign_id", str(campaign_id))
        
        if active_only:
            query = query.eq("is_active", True)
        
        result = query.order("step_number").execute()
        return result.data
    
    async def get_step(
        self, 
        campaign_id: UUID, 
        step_number: int
    ) -> Optional[dict]:
        """Get a specific step by campaign and step number."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("campaign_id", str(campaign_id))\
            .eq("step_number", step_number)\
            .execute()
        return result.data[0] if result.data else None
    
    async def get_next_step(
        self, 
        campaign_id: UUID, 
        current_step: int
    ) -> Optional[dict]:
        """Get the next active step after current step."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("campaign_id", str(campaign_id))\
            .eq("is_active", True)\
            .gt("step_number", current_step)\
            .order("step_number")\
            .limit(1)\
            .execute()
        return result.data[0] if result.data else None
    
    async def update(
        self, 
        sequence_id: UUID, 
        data: CampaignSequenceUpdate
    ) -> Optional[dict]:
        """Update a sequence step."""
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(sequence_id)
        
        # Convert UUID fields
        uuid_fields = ["email_template_id", "ab_test_group_id"]
        for field in uuid_fields:
            if field in update_data and update_data[field]:
                update_data[field] = str(update_data[field])
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(sequence_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def update_metrics(
        self, 
        sequence_id: UUID, 
        data: CampaignSequenceUpdateMetrics
    ) -> Optional[dict]:
        """Update sequence step metrics."""
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(sequence_id)
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(sequence_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def activate(self, sequence_id: UUID) -> Optional[dict]:
        """Activate a sequence step."""
        result = self.client.table(self.table)\
            .update({"is_active": True})\
            .eq("id", str(sequence_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def deactivate(self, sequence_id: UUID) -> Optional[dict]:
        """Deactivate a sequence step."""
        result = self.client.table(self.table)\
            .update({"is_active": False})\
            .eq("id", str(sequence_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def reorder(
        self, 
        campaign_id: UUID, 
        sequence_id: UUID, 
        new_step_number: int
    ) -> Optional[dict]:
        """Change the step number (reorder)."""
        result = self.client.table(self.table)\
            .update({"step_number": new_step_number})\
            .eq("id", str(sequence_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def delete(self, sequence_id: UUID) -> bool:
        """Delete a sequence step."""
        result = self.client.table(self.table)\
            .delete()\
            .eq("id", str(sequence_id))\
            .execute()
        return len(result.data) > 0 if result.data else False
    
    async def delete_by_campaign(self, campaign_id: UUID) -> int:
        """Delete all sequence steps for a campaign."""
        result = self.client.table(self.table)\
            .delete()\
            .eq("campaign_id", str(campaign_id))\
            .execute()
        return len(result.data) if result.data else 0
    
    async def count_by_campaign(self, campaign_id: UUID) -> int:
        """Count steps in a campaign."""
        result = self.client.table(self.table)\
            .select("id", count="exact")\
            .eq("campaign_id", str(campaign_id))\
            .execute()
        return result.count or 0
    
    async def get_max_step_number(self, campaign_id: UUID) -> int:
        """Get the maximum step number in a campaign."""
        result = self.client.table(self.table)\
            .select("step_number")\
            .eq("campaign_id", str(campaign_id))\
            .order("step_number", desc=True)\
            .limit(1)\
            .execute()
        
        if result.data:
            return result.data[0].get("step_number", 0)
        return 0
    
    async def increment_metric(
        self, 
        sequence_id: UUID, 
        metric: str, 
        amount: int = 1
    ) -> Optional[dict]:
        """Increment a specific metric."""
        current = await self.get_by_id(sequence_id)
        if not current:
            return None
        
        current_value = current.get(metric, 0) or 0
        update_data = {metric: current_value + amount}
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(sequence_id))\
            .execute()
        return result.data[0] if result.data else None
