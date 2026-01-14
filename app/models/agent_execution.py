"""AgentExecution model - Track agent task executions."""
from sqlalchemy import Column, String, Text, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class AgentExecution(Base):
    """Track each agent task execution."""
    
    __tablename__ = "agent_executions"
    
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
        ForeignKey("agents.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    tenant_agent_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("tenant_agents.id", ondelete="SET NULL"), 
        nullable=True
    )
    workflow_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("workflows.id", ondelete="SET NULL"), 
        nullable=True
    )
    triggered_by = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    # Task identification
    task_type = Column(String(100), nullable=False, index=True)
    task_name = Column(String(255), nullable=True)
    
    # Input/Output
    input_data = Column(JSONB, default=dict)
    output_data = Column(JSONB, default=dict)
    
    # Status
    status = Column(String(20), default="pending", index=True)
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, nullable=True)
    
    # Timing
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    # AI/LLM metrics
    model_used = Column(String(100), nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(Numeric(10, 6), default=0)
    
    # Crew AI specific
    crew_run_id = Column(String(100), nullable=True)
    crew_steps = Column(JSONB, default=list)
    
    # Related entities
    lead_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    campaign_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Quality metrics
    confidence_score = Column(Numeric(3, 2), nullable=True)
    quality_rating = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    
    @property
    def is_running(self) -> bool:
        """Check if execution is running."""
        return self.status == "running"
    
    @property
    def is_completed(self) -> bool:
        """Check if execution completed successfully."""
        return self.status == "completed"
    
    @property
    def is_failed(self) -> bool:
        """Check if execution failed."""
        return self.status == "failed"
    
    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        if self.duration_ms:
            return self.duration_ms / 1000
        return 0.0
