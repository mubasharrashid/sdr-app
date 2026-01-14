"""
Agent Model - Master agent definitions for the platform.

Defines the three core agents: Jules (Marketing), Joy (Sales), George (Customer Success).
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class Agent(Base):
    """
    Master agent definitions table.
    
    Contains the three core AI agents and their configurations.
    """
    
    __tablename__ = "agents"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Agent identification
    slug = Column(
        String(50), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="URL-safe identifier: jules, joy, george"
    )
    name = Column(String(100), nullable=False, comment="Display name")
    
    # Description & Category
    description = Column(Text, comment="Agent description")
    category = Column(
        String(50), 
        nullable=False, 
        index=True,
        comment="Category: marketing, sales, customer_success"
    )
    
    # Capabilities
    capabilities = Column(
        JSON, 
        default=list,
        comment="JSON array of agent capabilities"
    )
    
    # AI Configuration
    system_prompt = Column(Text, comment="Default system prompt for AI model")
    default_model = Column(String(50), default="gpt-4", comment="Default LLM model")
    default_temperature = Column(Numeric(3, 2), default=0.7, comment="Default temperature")
    
    # Status
    is_active = Column(Boolean, default=True, index=True, comment="Whether agent is available")
    
    # UI Metadata
    icon_url = Column(Text, comment="URL to agent icon")
    color = Column(String(7), comment="Hex color for UI")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
    
    def __repr__(self) -> str:
        return f"<Agent(slug='{self.slug}', name='{self.name}')>"
    
    @property
    def is_marketing(self) -> bool:
        """Check if this is the marketing agent (Jules)."""
        return self.slug == "jules"
    
    @property
    def is_sales(self) -> bool:
        """Check if this is the sales agent (Joy)."""
        return self.slug == "joy"
    
    @property
    def is_customer_success(self) -> bool:
        """Check if this is the customer success agent (George)."""
        return self.slug == "george"
