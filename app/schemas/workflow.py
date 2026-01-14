"""Pydantic schemas for Workflow."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class WorkflowBase(BaseModel):
    """Base schema for Workflow."""
    
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    workflow_type: str = Field(..., pattern="^(trigger|action|scheduled|manual)$")
    trigger_event: Optional[str] = Field(None, max_length=100)
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    input_schema: Optional[Dict[str, Any]] = Field(default_factory=dict)
    output_schema: Optional[Dict[str, Any]] = Field(default_factory=dict)
    schedule_cron: Optional[str] = Field(None, max_length=100)


class WorkflowCreate(WorkflowBase):
    """Schema for creating a Workflow."""
    
    agent_id: Optional[UUID] = None
    n8n_workflow_id: Optional[str] = Field(None, max_length=100)
    n8n_webhook_url: Optional[str] = None
    is_enabled: bool = True


class WorkflowCreateInternal(WorkflowCreate):
    """Internal schema for creating a Workflow."""
    
    tenant_id: str
    created_by: Optional[str] = None


class WorkflowUpdate(BaseModel):
    """Schema for updating a Workflow."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    agent_id: Optional[UUID] = None
    n8n_workflow_id: Optional[str] = Field(None, max_length=100)
    n8n_webhook_url: Optional[str] = None
    workflow_type: Optional[str] = Field(None, pattern="^(trigger|action|scheduled|manual)$")
    trigger_event: Optional[str] = Field(None, max_length=100)
    config: Optional[Dict[str, Any]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, pattern="^(draft|active|paused|archived)$")
    is_enabled: Optional[bool] = None
    schedule_cron: Optional[str] = Field(None, max_length=100)
    next_scheduled_at: Optional[datetime] = None


class WorkflowUpdateExecution(BaseModel):
    """Internal schema for updating execution stats."""
    
    total_executions: Optional[int] = None
    successful_executions: Optional[int] = None
    failed_executions: Optional[int] = None
    last_executed_at: Optional[datetime] = None
    last_error: Optional[str] = None


class WorkflowResponse(BaseModel):
    """Response schema for Workflow."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    agent_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    n8n_workflow_id: Optional[str] = None
    n8n_webhook_url: Optional[str] = None
    workflow_type: str
    trigger_event: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    status: str
    is_enabled: bool
    total_executions: int
    successful_executions: int
    failed_executions: int
    last_executed_at: Optional[datetime] = None
    last_error: Optional[str] = None
    schedule_cron: Optional[str] = None
    next_scheduled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    
    # Computed
    is_active: Optional[bool] = None
    is_scheduled: Optional[bool] = None
    success_rate: Optional[float] = None


class WorkflowSummary(BaseModel):
    """Summary schema for Workflow."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    workflow_type: str
    status: str
    is_enabled: bool
    total_executions: int
    last_executed_at: Optional[datetime] = None


class WorkflowListResponse(BaseModel):
    """List response for Workflows."""
    
    items: List[WorkflowResponse]
    total: int
