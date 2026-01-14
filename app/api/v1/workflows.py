"""API endpoints for Workflows."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from uuid import UUID

from supabase import create_client, Client

from app.core.config import settings
from app.repositories.workflow import WorkflowRepository
from app.repositories.tenant import TenantRepository
from app.repositories.agent import AgentRepository
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowCreateInternal,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowSummary,
    WorkflowListResponse
)

router = APIRouter(prefix="/workflows", tags=["workflows"])


def get_supabase() -> Client:
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_workflow_repo(
    supabase: Client = Depends(get_supabase)
) -> WorkflowRepository:
    """Get WorkflowRepository instance."""
    return WorkflowRepository(supabase)


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
    """Add computed fields to workflow data."""
    data["is_active"] = data.get("status") == "active" and data.get("is_enabled", False)
    data["is_scheduled"] = data.get("workflow_type") == "scheduled"
    
    total = data.get("total_executions", 0) or 0
    successful = data.get("successful_executions", 0) or 0
    data["success_rate"] = (successful / total * 100) if total > 0 else 0.0
    
    return data


@router.post("/tenants/{tenant_id}", response_model=WorkflowResponse)
async def create_workflow(
    tenant_id: UUID,
    data: WorkflowCreate,
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo),
    workflow_repo: WorkflowRepository = Depends(get_workflow_repo)
):
    """Create a new workflow."""
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Verify agent if provided
    if data.agent_id:
        agent = await agent_repo.get_by_id(data.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
    
    # Create workflow
    create_data = WorkflowCreateInternal(
        tenant_id=str(tenant_id),
        **data.model_dump(exclude_none=True)
    )
    
    workflow = await workflow_repo.create(create_data)
    return _add_computed_fields(workflow)


@router.get("/tenants/{tenant_id}", response_model=WorkflowListResponse)
async def list_workflows(
    tenant_id: UUID,
    status: Optional[str] = Query(None, description="Filter by status"),
    workflow_type: Optional[str] = Query(None, description="Filter by type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    workflow_repo: WorkflowRepository = Depends(get_workflow_repo)
):
    """List all workflows for a tenant."""
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    items, total = await workflow_repo.get_by_tenant(
        tenant_id, 
        status=status, 
        workflow_type=workflow_type,
        skip=skip, 
        limit=limit
    )
    return WorkflowListResponse(
        items=[_add_computed_fields(i) for i in items],
        total=total
    )


@router.get("/tenants/{tenant_id}/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    tenant_id: UUID,
    workflow_id: UUID,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repo)
):
    """Get a specific workflow."""
    workflow = await workflow_repo.get_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if str(workflow.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Workflow belongs to another tenant")
    
    return _add_computed_fields(workflow)


@router.patch("/tenants/{tenant_id}/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    tenant_id: UUID,
    workflow_id: UUID,
    data: WorkflowUpdate,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repo),
    agent_repo: AgentRepository = Depends(get_agent_repo)
):
    """Update a workflow."""
    workflow = await workflow_repo.get_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if str(workflow.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Workflow belongs to another tenant")
    
    # Verify agent if changing
    if data.agent_id:
        agent = await agent_repo.get_by_id(data.agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
    
    updated = await workflow_repo.update(workflow_id, data)
    return _add_computed_fields(updated)


@router.post("/tenants/{tenant_id}/{workflow_id}/activate", response_model=WorkflowResponse)
async def activate_workflow(
    tenant_id: UUID,
    workflow_id: UUID,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repo)
):
    """Activate a workflow."""
    workflow = await workflow_repo.get_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if str(workflow.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Workflow belongs to another tenant")
    
    activated = await workflow_repo.activate(workflow_id)
    return _add_computed_fields(activated)


@router.post("/tenants/{tenant_id}/{workflow_id}/pause", response_model=WorkflowResponse)
async def pause_workflow(
    tenant_id: UUID,
    workflow_id: UUID,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repo)
):
    """Pause a workflow."""
    workflow = await workflow_repo.get_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if str(workflow.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Workflow belongs to another tenant")
    
    paused = await workflow_repo.pause(workflow_id)
    return _add_computed_fields(paused)


@router.post("/tenants/{tenant_id}/{workflow_id}/archive", response_model=WorkflowResponse)
async def archive_workflow(
    tenant_id: UUID,
    workflow_id: UUID,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repo)
):
    """Archive a workflow."""
    workflow = await workflow_repo.get_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if str(workflow.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Workflow belongs to another tenant")
    
    archived = await workflow_repo.archive(workflow_id)
    return _add_computed_fields(archived)


@router.delete("/tenants/{tenant_id}/{workflow_id}")
async def delete_workflow(
    tenant_id: UUID,
    workflow_id: UUID,
    workflow_repo: WorkflowRepository = Depends(get_workflow_repo)
):
    """Delete a workflow."""
    workflow = await workflow_repo.get_by_id(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if str(workflow.get("tenant_id")) != str(tenant_id):
        raise HTTPException(status_code=403, detail="Workflow belongs to another tenant")
    
    await workflow_repo.delete(workflow_id)
    return {"message": "Workflow deleted"}


# ============================================================================
# Agent Workflows
# ============================================================================

@router.get("/agents/{agent_id}", response_model=List[WorkflowSummary])
async def list_agent_workflows(
    agent_id: UUID,
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    agent_repo: AgentRepository = Depends(get_agent_repo),
    workflow_repo: WorkflowRepository = Depends(get_workflow_repo)
):
    """List all workflows for an agent."""
    # Verify agent exists
    agent = await agent_repo.get_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    workflows = await workflow_repo.get_by_agent(agent_id, tenant_id)
    return workflows


# ============================================================================
# Trigger-based Workflows
# ============================================================================

@router.get("/triggers/{trigger_event}", response_model=List[WorkflowSummary])
async def list_workflows_by_trigger(
    trigger_event: str,
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    workflow_repo: WorkflowRepository = Depends(get_workflow_repo)
):
    """List active workflows for a trigger event."""
    workflows = await workflow_repo.get_by_trigger(trigger_event, tenant_id)
    return workflows
