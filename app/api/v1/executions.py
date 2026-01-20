"""API endpoints for Agent Executions."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID

from supabase import create_client, Client

from app.core.config import settings
from app.repositories.agent_execution import AgentExecutionRepository
from app.repositories.tenant import TenantRepository
from app.repositories.agent import AgentRepository
from app.repositories.tenant_agent import TenantAgentRepository
from app.schemas.agent_execution import (
    AgentExecutionCreate,
    AgentExecutionCreateInternal,
    AgentExecutionUpdate,
    AgentExecutionUpdateMetrics,
    AgentExecutionFeedback,
    AgentExecutionResponse,
    AgentExecutionListResponse,
    AgentExecutionStats
)
from app.schemas.response import ApiResponse
from app.core.response_helpers import success_response, paginated_response

router = APIRouter(prefix="/executions", tags=["executions"])


def get_supabase() -> Client:
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_execution_repo(
    supabase: Client = Depends(get_supabase)
) -> AgentExecutionRepository:
    """Get AgentExecutionRepository instance."""
    return AgentExecutionRepository(supabase)


def get_tenant_repo(
    supabase: Client = Depends(get_supabase)
) -> TenantRepository:
    """Get TenantRepository instance."""
    return TenantRepository(supabase)


def get_agent_repo(
    supabase: Client = Depends(get_supabase)
) -> AgentRepository:
    """Get AgentRepository instance."""
    return AgentRepository(supabase)


def _add_computed_fields(data: dict) -> dict:
    """Add computed fields to execution data."""
    data["is_running"] = data.get("status") == "running"
    data["is_completed"] = data.get("status") == "completed"
    data["is_failed"] = data.get("status") == "failed"
    
    duration_ms = data.get("duration_ms")
    data["duration_seconds"] = duration_ms / 1000 if duration_ms else 0.0
    
    return data


@router.post("/tenants/{tenant_id}", response_model=ApiResponse)
async def create_execution(
    tenant_id: UUID,
    data: AgentExecutionCreate,
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo),
    execution_repo: AgentExecutionRepository = Depends(get_execution_repo)
):
    """Create a new agent execution."""
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Verify agent exists
    agent = await agent_repo.get_by_id(data.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    create_data = AgentExecutionCreateInternal(
        tenant_id=str(tenant_id),
        **data.model_dump(exclude_none=True)
    )
    
    execution = await execution_repo.create(create_data)
    return success_response(data=_add_computed_fields(execution), message="Execution created successfully", status_code=201)


@router.get("/tenants/{tenant_id}", response_model=ApiResponse)
async def list_executions(
    tenant_id: UUID,
    status: Optional[str] = Query(None, description="Filter by status"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    agent_id: Optional[UUID] = Query(None, description="Filter by agent"),
    page: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(10, ge=1, le=100, description="Items per page"),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    execution_repo: AgentExecutionRepository = Depends(get_execution_repo)
):
    """List agent executions for a tenant."""
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    skip = (page - 1) * pageSize
    items, total = await execution_repo.get_by_tenant(
        tenant_id, 
        status=status,
        task_type=task_type,
        agent_id=agent_id,
        skip=skip, 
        limit=pageSize
    )
    return paginated_response(
        items=[_add_computed_fields(i) for i in items],
        total=total,
        page=page,
        page_size=pageSize,
        message="Executions retrieved successfully"
    )


@router.get("/tenants/{tenant_id}/stats", response_model=ApiResponse)
async def get_execution_stats(
    tenant_id: UUID,
    agent_id: Optional[UUID] = Query(None, description="Filter by agent"),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    execution_repo: AgentExecutionRepository = Depends(get_execution_repo)
):
    """Get execution statistics for a tenant."""
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    stats = await execution_repo.get_stats(tenant_id, agent_id)
    return success_response(data=stats, message="Execution statistics retrieved successfully")


@router.get("/tenants/{tenant_id}/{execution_id}", response_model=ApiResponse)
async def get_execution(
    tenant_id: UUID,
    execution_id: UUID,
    execution_repo: AgentExecutionRepository = Depends(get_execution_repo)
):
    """Get a specific execution."""
    execution = await execution_repo.get_by_id(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if str(execution.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Execution belongs to another tenant")
    
    return success_response(data=_add_computed_fields(execution), message="Execution retrieved successfully")


@router.post("/tenants/{tenant_id}/{execution_id}/start", response_model=ApiResponse)
async def start_execution(
    tenant_id: UUID,
    execution_id: UUID,
    execution_repo: AgentExecutionRepository = Depends(get_execution_repo)
):
    """Start an execution."""
    execution = await execution_repo.get_by_id(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if str(execution.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Execution belongs to another tenant")
    
    if execution.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Execution is not in pending status")
    
    started = await execution_repo.start(execution_id)
    return success_response(data=_add_computed_fields(started), message="Execution started successfully")


@router.post("/tenants/{tenant_id}/{execution_id}/complete", response_model=ApiResponse)
async def complete_execution(
    tenant_id: UUID,
    execution_id: UUID,
    output_data: dict,
    duration_ms: int,
    execution_repo: AgentExecutionRepository = Depends(get_execution_repo)
):
    """Complete an execution successfully."""
    execution = await execution_repo.get_by_id(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if str(execution.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Execution belongs to another tenant")
    
    completed = await execution_repo.complete(execution_id, output_data, duration_ms)
    return success_response(data=_add_computed_fields(completed), message="Execution completed successfully")


@router.post("/tenants/{tenant_id}/{execution_id}/fail", response_model=ApiResponse)
async def fail_execution(
    tenant_id: UUID,
    execution_id: UUID,
    error_message: str,
    error_details: Optional[dict] = None,
    execution_repo: AgentExecutionRepository = Depends(get_execution_repo)
):
    """Mark execution as failed."""
    execution = await execution_repo.get_by_id(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if str(execution.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Execution belongs to another tenant")
    
    failed = await execution_repo.fail(execution_id, error_message, error_details)
    return success_response(data=_add_computed_fields(failed), message="Execution marked as failed")


@router.patch("/tenants/{tenant_id}/{execution_id}/metrics", response_model=ApiResponse)
async def update_metrics(
    tenant_id: UUID,
    execution_id: UUID,
    data: AgentExecutionUpdateMetrics,
    execution_repo: AgentExecutionRepository = Depends(get_execution_repo)
):
    """Update AI/LLM metrics for an execution."""
    execution = await execution_repo.get_by_id(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if str(execution.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Execution belongs to another tenant")
    
    updated = await execution_repo.update_metrics(execution_id, data)
    return success_response(data=_add_computed_fields(updated), message="Execution metrics updated successfully")


@router.post("/tenants/{tenant_id}/{execution_id}/feedback", response_model=ApiResponse)
async def add_feedback(
    tenant_id: UUID,
    execution_id: UUID,
    data: AgentExecutionFeedback,
    execution_repo: AgentExecutionRepository = Depends(get_execution_repo)
):
    """Add user feedback to an execution."""
    execution = await execution_repo.get_by_id(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if str(execution.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Execution belongs to another tenant")
    
    updated = await execution_repo.add_feedback(execution_id, data)
    return success_response(data=_add_computed_fields(updated), message="Feedback added successfully")
