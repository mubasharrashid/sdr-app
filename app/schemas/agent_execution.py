"""Pydantic schemas for AgentExecution."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class AgentExecutionBase(BaseModel):
    """Base schema for AgentExecution."""
    
    task_type: str = Field(..., min_length=1, max_length=100)
    task_name: Optional[str] = Field(None, max_length=255)
    input_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AgentExecutionCreate(AgentExecutionBase):
    """Schema for creating an AgentExecution."""
    
    agent_id: UUID
    workflow_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None
    campaign_id: Optional[UUID] = None


class AgentExecutionCreateInternal(AgentExecutionCreate):
    """Internal schema for creating an AgentExecution."""
    
    tenant_id: str
    tenant_agent_id: Optional[str] = None
    triggered_by: Optional[str] = None
    status: str = "pending"


class AgentExecutionUpdate(BaseModel):
    """Schema for updating an AgentExecution."""
    
    status: Optional[str] = Field(None, pattern="^(pending|running|completed|failed|cancelled)$")
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


class AgentExecutionUpdateMetrics(BaseModel):
    """Schema for updating AI metrics."""
    
    model_used: Optional[str] = Field(None, max_length=100)
    prompt_tokens: Optional[int] = Field(None, ge=0)
    completion_tokens: Optional[int] = Field(None, ge=0)
    total_tokens: Optional[int] = Field(None, ge=0)
    estimated_cost: Optional[Decimal] = None
    crew_run_id: Optional[str] = Field(None, max_length=100)
    crew_steps: Optional[List[Dict[str, Any]]] = None
    confidence_score: Optional[Decimal] = Field(None, ge=0, le=1)


class AgentExecutionFeedback(BaseModel):
    """Schema for providing feedback."""
    
    quality_rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


class AgentExecutionResponse(BaseModel):
    """Response schema for AgentExecution."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    tenant_id: UUID
    agent_id: UUID
    tenant_agent_id: Optional[UUID] = None
    workflow_id: Optional[UUID] = None
    triggered_by: Optional[UUID] = None
    task_type: str
    task_name: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    status: str
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    model_used: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: Optional[Decimal] = None
    crew_run_id: Optional[str] = None
    lead_id: Optional[UUID] = None
    campaign_id: Optional[UUID] = None
    confidence_score: Optional[Decimal] = None
    quality_rating: Optional[int] = None
    feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed
    is_running: Optional[bool] = None
    is_completed: Optional[bool] = None
    is_failed: Optional[bool] = None
    duration_seconds: Optional[float] = None


class AgentExecutionSummary(BaseModel):
    """Summary schema for AgentExecution."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    agent_id: UUID
    task_type: str
    task_name: Optional[str] = None
    status: str
    duration_ms: Optional[int] = None
    created_at: datetime


class AgentExecutionListResponse(BaseModel):
    """List response for AgentExecutions."""
    
    items: List[AgentExecutionResponse]
    total: int


class AgentExecutionStats(BaseModel):
    """Statistics for agent executions."""
    
    total_executions: int = 0
    completed: int = 0
    failed: int = 0
    running: int = 0
    avg_duration_ms: Optional[float] = None
    total_tokens: int = 0
    total_cost: Decimal = Decimal("0")
