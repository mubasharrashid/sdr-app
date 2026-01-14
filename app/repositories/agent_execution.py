"""Repository for AgentExecution CRUD operations."""
from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime, timezone
from decimal import Decimal

from app.schemas.agent_execution import (
    AgentExecutionCreateInternal,
    AgentExecutionUpdate,
    AgentExecutionUpdateMetrics,
    AgentExecutionFeedback,
    AgentExecutionStats
)


class AgentExecutionRepository:
    """Repository for AgentExecution operations."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.table = "agent_executions"
    
    async def create(self, data: AgentExecutionCreateInternal) -> dict:
        """Create a new agent execution."""
        insert_data = data.model_dump(exclude_none=True)
        
        # Convert UUIDs to strings
        uuid_fields = ["tenant_id", "agent_id", "tenant_agent_id", "workflow_id", 
                       "triggered_by", "lead_id", "campaign_id"]
        for field in uuid_fields:
            if field in insert_data and insert_data[field] is not None:
                insert_data[field] = str(insert_data[field])
        
        result = self.client.table(self.table).insert(insert_data).execute()
        return result.data[0] if result.data else None
    
    async def get_by_id(self, execution_id: UUID) -> Optional[dict]:
        """Get execution by ID."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("id", str(execution_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def get_by_tenant(
        self, 
        tenant_id: UUID,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
        agent_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[dict], int]:
        """Get all executions for a tenant."""
        query = self.client.table(self.table)\
            .select("*", count="exact")\
            .eq("tenant_id", str(tenant_id))
        
        if status:
            query = query.eq("status", status)
        if task_type:
            query = query.eq("task_type", task_type)
        if agent_id:
            query = query.eq("agent_id", str(agent_id))
        
        result = query.order("created_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()
        return result.data, result.count or 0
    
    async def get_by_agent(
        self, 
        agent_id: UUID,
        tenant_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[dict], int]:
        """Get executions for an agent."""
        query = self.client.table(self.table)\
            .select("*", count="exact")\
            .eq("agent_id", str(agent_id))
        
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        
        result = query.order("created_at", desc=True)\
            .range(skip, skip + limit - 1)\
            .execute()
        return result.data, result.count or 0
    
    async def get_by_lead(self, lead_id: UUID) -> List[dict]:
        """Get all executions for a lead."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("lead_id", str(lead_id))\
            .order("created_at", desc=True)\
            .execute()
        return result.data
    
    async def get_by_workflow(self, workflow_id: UUID) -> List[dict]:
        """Get all executions for a workflow."""
        result = self.client.table(self.table)\
            .select("*")\
            .eq("workflow_id", str(workflow_id))\
            .order("created_at", desc=True)\
            .execute()
        return result.data
    
    async def start(self, execution_id: UUID) -> Optional[dict]:
        """Mark execution as running."""
        update_data = {
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat()
        }
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(execution_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def complete(
        self,
        execution_id: UUID,
        output_data: dict,
        duration_ms: int
    ) -> Optional[dict]:
        """Mark execution as completed."""
        update_data = {
            "status": "completed",
            "output_data": output_data,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration_ms
        }
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(execution_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def fail(
        self,
        execution_id: UUID,
        error_message: str,
        error_details: Optional[dict] = None
    ) -> Optional[dict]:
        """Mark execution as failed."""
        current = await self.get_by_id(execution_id)
        started_at = current.get("started_at") if current else None
        
        duration_ms = None
        if started_at:
            try:
                start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                duration_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)
            except:
                pass
        
        update_data = {
            "status": "failed",
            "error_message": error_message,
            "error_details": error_details,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration_ms
        }
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(execution_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def cancel(self, execution_id: UUID) -> Optional[dict]:
        """Cancel an execution."""
        update_data = {
            "status": "cancelled",
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(execution_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def update_metrics(
        self,
        execution_id: UUID,
        data: AgentExecutionUpdateMetrics
    ) -> Optional[dict]:
        """Update AI/LLM metrics."""
        update_data = data.model_dump(exclude_none=True)
        if not update_data:
            return await self.get_by_id(execution_id)
        
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(execution_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def add_feedback(
        self,
        execution_id: UUID,
        data: AgentExecutionFeedback
    ) -> Optional[dict]:
        """Add user feedback."""
        update_data = {
            "quality_rating": data.quality_rating,
            "feedback": data.feedback
        }
        result = self.client.table(self.table)\
            .update(update_data)\
            .eq("id", str(execution_id))\
            .execute()
        return result.data[0] if result.data else None
    
    async def get_stats(
        self, 
        tenant_id: UUID,
        agent_id: Optional[UUID] = None
    ) -> AgentExecutionStats:
        """Get execution statistics."""
        query = self.client.table(self.table)\
            .select("status, duration_ms, total_tokens, estimated_cost")\
            .eq("tenant_id", str(tenant_id))
        
        if agent_id:
            query = query.eq("agent_id", str(agent_id))
        
        result = query.execute()
        
        stats = AgentExecutionStats()
        durations = []
        
        for exec in result.data:
            stats.total_executions += 1
            status = exec.get("status")
            if status == "completed":
                stats.completed += 1
            elif status == "failed":
                stats.failed += 1
            elif status == "running":
                stats.running += 1
            
            if exec.get("duration_ms"):
                durations.append(exec["duration_ms"])
            stats.total_tokens += exec.get("total_tokens", 0) or 0
            stats.total_cost += Decimal(str(exec.get("estimated_cost", 0) or 0))
        
        if durations:
            stats.avg_duration_ms = sum(durations) / len(durations)
        
        return stats
    
    async def delete(self, execution_id: UUID) -> bool:
        """Delete an execution."""
        result = self.client.table(self.table)\
            .delete()\
            .eq("id", str(execution_id))\
            .execute()
        return len(result.data) > 0 if result.data else False
