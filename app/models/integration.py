"""Integration model - Master list of available integrations."""
from sqlalchemy import Column, String, Text, Boolean, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.db.base_class import Base


class Integration(Base):
    """Master integration definition."""
    
    __tablename__ = "integrations"
    
    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Identification
    slug = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Categorization
    category = Column(String(50), nullable=False, index=True)
    
    # Provider info
    provider = Column(String(100), nullable=True)
    provider_url = Column(Text, nullable=True)
    
    # Authentication
    auth_type = Column(String(20), nullable=False)  # oauth2, api_key, basic, webhook
    
    # OAuth config
    oauth_authorization_url = Column(Text, nullable=True)
    oauth_token_url = Column(Text, nullable=True)
    oauth_scopes = Column(ARRAY(Text), nullable=True)
    
    # Required fields for API key auth
    required_fields = Column(JSONB, default=list)
    
    # UI metadata
    icon_url = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_premium = Column(Boolean, default=False)
    
    # Documentation
    docs_url = Column(Text, nullable=True)
    setup_instructions = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(UUID, server_default=func.now())
    updated_at = Column(UUID, server_default=func.now(), onupdate=func.now())
    
    @property
    def is_oauth(self) -> bool:
        """Check if integration uses OAuth."""
        return self.auth_type == "oauth2"
    
    @property
    def is_api_key(self) -> bool:
        """Check if integration uses API key."""
        return self.auth_type == "api_key"
