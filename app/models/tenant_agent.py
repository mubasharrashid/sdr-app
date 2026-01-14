"""
TenantAgent Model - Links tenants to their assigned AI agents.

Supports per-tenant agent customization and usage tracking.
"""

from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, JSON, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class TenantAgent(Base):
    """
    Junction table linking tenants to agents.
    
    Each tenant can have one or more agents assigned (currently limited to one).
    Supports per-tenant customization of agent prompts and settings.
    """
    
    __tablename__ = "tenant_agents"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relationships
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to tenants table"
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to agents table"
    )
    
    # Status
    is_active = Column(
        Boolean, 
        default=True, 
        comment="Whether this agent is currently active for the tenant"
    )
    
    # Per-tenant customization
    custom_system_prompt = Column(
        Text, 
        comment="Override the agent's default system prompt"
    )
    custom_model = Column(
        String(50), 
        comment="Override the agent's default LLM model"
    )
    custom_temperature = Column(
        Numeric(3, 2), 
        comment="Override the agent's default temperature"
    )
    
    # Agent-specific settings
    settings = Column(
        JSON, 
        default=dict,
        comment="Tenant-specific agent settings"
    )
    
    # Usage tracking
    total_executions = Column(
        Integer, 
        default=0, 
        comment="Total number of agent executions"
    )
    last_execution_at = Column(
        DateTime(timezone=True), 
        comment="Last time the agent was executed"
    )
    
    # Activation tracking
    activated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        comment="When this agent was activated for the tenant"
    )
    deactivated_at = Column(
        DateTime(timezone=True), 
        comment="When this agent was deactivated"
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    # Relationships
    # tenant = relationship("Tenant", back_populates="tenant_agents")
    # agent = relationship("Agent", back_populates="tenant_agents")
    
    def __repr__(self) -> str:
        return f"<TenantAgent(tenant_id={self.tenant_id}, agent_id={self.agent_id}, is_active={self.is_active})>"
    
    @property
    def has_custom_prompt(self) -> bool:
        """Check if tenant has a custom prompt for this agent."""
        return self.custom_system_prompt is not None
    
    @property
    def has_custom_model(self) -> bool:
        """Check if tenant has a custom model setting."""
        return self.custom_model is not None
