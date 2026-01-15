"""Repository for LeadAIConversation CRUD operations."""
from typing import Optional, List, Tuple
from uuid import UUID

from app.schemas.lead_ai_conversation import LeadAIConversationCreateInternal


class LeadAIConversationRepository:
    """Repository for LeadAIConversation operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "leads_ai_conversation"
    
    async def create(self, data: LeadAIConversationCreateInternal) -> dict:
        """Create a new conversation entry."""
        insert_data = data.model_dump(exclude_none=True)
        
        uuid_fields = ["tenant_id", "lead_id", "agent_id", "execution_id", 
                       "campaign_id", "call_task_id", "email_reply_id"]
        for field in uuid_fields:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = str(insert_data[field])
        
        if "sent_at" in insert_data and insert_data["sent_at"]:
            insert_data["sent_at"] = insert_data["sent_at"].isoformat()
        
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, conversation_id: UUID) -> Optional[dict]:
        """Get conversation by ID."""
        result = self.client.table(self.table).select("*").eq("id", str(conversation_id)).execute()
        return result.data[0] if result.data else None
    
    async def get_by_lead(
        self, lead_id: UUID, channel: Optional[str] = None,
        skip: int = 0, limit: int = 100
    ) -> Tuple[List[dict], int]:
        """Get conversation history for a lead."""
        query = self.client.table(self.table).select("*", count="exact").eq("lead_id", str(lead_id))
        if channel:
            query = query.eq("channel", channel)
        result = query.order("created_at").range(skip, skip + limit - 1).execute()
        return result.data, result.count or 0
    
    async def get_recent_for_lead(self, lead_id: UUID, limit: int = 10) -> List[dict]:
        """Get most recent conversation for a lead."""
        result = self.client.table(self.table).select("*")\
            .eq("lead_id", str(lead_id)).order("created_at", desc=True).limit(limit).execute()
        return result.data
    
    async def get_by_agent(
        self, agent_id: UUID, tenant_id: Optional[UUID] = None,
        skip: int = 0, limit: int = 50
    ) -> Tuple[List[dict], int]:
        """Get conversations by agent."""
        query = self.client.table(self.table).select("*", count="exact").eq("agent_id", str(agent_id))
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        result = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        return result.data, result.count or 0
    
    async def get_by_execution(self, execution_id: UUID) -> List[dict]:
        """Get conversations for an execution."""
        result = self.client.table(self.table).select("*")\
            .eq("execution_id", str(execution_id)).order("created_at").execute()
        return result.data
    
    async def delete(self, conversation_id: UUID) -> bool:
        """Delete a conversation entry."""
        result = self.client.table(self.table).delete().eq("id", str(conversation_id)).execute()
        return len(result.data) > 0 if result.data else False
    
    async def delete_by_lead(self, lead_id: UUID) -> int:
        """Delete all conversations for a lead."""
        result = self.client.table(self.table).delete().eq("lead_id", str(lead_id)).execute()
        return len(result.data) if result.data else 0
    
    async def count_by_lead(self, lead_id: UUID) -> int:
        """Count conversations for a lead."""
        result = self.client.table(self.table).select("id", count="exact").eq("lead_id", str(lead_id)).execute()
        return result.count or 0
