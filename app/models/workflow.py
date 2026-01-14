"""Workflow model - n8n workflow references."""
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class Workflow(Base):
    """n8n workflow reference and automation definition."""
    
    __tablename__ = "workflows"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    tenant_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("tenants.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    agent_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("agents.id", ondelete="SET NULL"), 
        nullable=True,
        index=True
    )
    
    # Identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # n8n reference
    n8n_workflow_id = Column(String(100), nullable=True, index=True)
    n8n_webhook_url = Column(Text, nullable=True)
    
    # Type
    workflow_type = Column(String(50), nullable=False, index=True)
    trigger_event = Column(String(100), nullable=True, index=True)
    
    # Configuration
    config = Column(JSONB, default=dict)
    input_schema = Column(JSONB, default=dict)
    output_schema = Column(JSONB, default=dict)
    
    # Status
    status = Column(String(20), default="draft", index=True)
    is_enabled = Column(Boolean, default=True)
    
    # Execution tracking
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    last_executed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Scheduling
    schedule_cron = Column(String(100), nullable=True)
    next_scheduled_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    @property
    def is_active(self) -> bool:
        """Check if workflow is active."""
        return self.status == "active" and self.is_enabled
    
    @property
    def is_scheduled(self) -> bool:
        """Check if workflow is scheduled type."""
        return self.workflow_type == "scheduled"
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100
