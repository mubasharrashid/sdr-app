"""Pydantic schemas for CampaignSequence."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class CampaignSequenceBase(BaseModel):
    """Base schema for CampaignSequence."""
    
    step_number: int = Field(..., ge=1)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    step_type: str = Field(..., pattern="^(email|call|linkedin_message|linkedin_connect|wait|condition)$")
    delay_days: int = Field(default=0, ge=0)
    delay_hours: int = Field(default=0, ge=0, le=23)
    delay_minutes: int = Field(default=0, ge=0, le=59)
    condition_type: Optional[str] = Field(None, pattern="^(none|if_no_reply|if_opened|if_clicked|if_replied)$")
    condition_value: Optional[Dict[str, Any]] = None
    use_ai_generation: bool = True
    is_active: bool = True


class CampaignSequenceCreate(CampaignSequenceBase):
    """Schema for creating a CampaignSequence."""
    
    # Email content
    email_subject: Optional[str] = Field(None, max_length=500)
    email_body: Optional[str] = None
    email_template_id: Optional[UUID] = None
    
    # Call script
    call_script: Optional[str] = None
    call_objective: Optional[str] = Field(None, max_length=255)
    
    # LinkedIn content
    linkedin_message: Optional[str] = None
    linkedin_connection_note: Optional[str] = Field(None, max_length=300)
    
    # AI settings
    ai_prompt_template: Optional[str] = None
    ai_variables: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # A/B testing
    is_ab_test: bool = False
    ab_variant: Optional[str] = Field(None, max_length=10)
    ab_test_group_id: Optional[UUID] = None


class CampaignSequenceCreateInternal(CampaignSequenceCreate):
    """Internal schema for creating a CampaignSequence."""
    
    campaign_id: str
    tenant_id: str


class CampaignSequenceUpdate(BaseModel):
    """Schema for updating a CampaignSequence."""
    
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    step_number: Optional[int] = Field(None, ge=1)
    delay_days: Optional[int] = Field(None, ge=0)
    delay_hours: Optional[int] = Field(None, ge=0, le=23)
    delay_minutes: Optional[int] = Field(None, ge=0, le=59)
    condition_type: Optional[str] = Field(None, pattern="^(none|if_no_reply|if_opened|if_clicked|if_replied)$")
    condition_value: Optional[Dict[str, Any]] = None
    
    # Email content
    email_subject: Optional[str] = Field(None, max_length=500)
    email_body: Optional[str] = None
    email_template_id: Optional[UUID] = None
    
    # Call script
    call_script: Optional[str] = None
    call_objective: Optional[str] = Field(None, max_length=255)
    
    # LinkedIn content
    linkedin_message: Optional[str] = None
    linkedin_connection_note: Optional[str] = Field(None, max_length=300)
    
    # AI settings
    use_ai_generation: Optional[bool] = None
    ai_prompt_template: Optional[str] = None
    ai_variables: Optional[Dict[str, Any]] = None
    
    # Status
    is_active: Optional[bool] = None
    
    # A/B testing
    is_ab_test: Optional[bool] = None
    ab_variant: Optional[str] = Field(None, max_length=10)
    ab_test_group_id: Optional[UUID] = None


class CampaignSequenceUpdateMetrics(BaseModel):
    """Schema for updating sequence step metrics."""
    
    total_sent: Optional[int] = None
    total_opened: Optional[int] = None
    total_clicked: Optional[int] = None
    total_replied: Optional[int] = None
    total_converted: Optional[int] = None


class CampaignSequenceResponse(BaseModel):
    """Response schema for CampaignSequence."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    campaign_id: UUID
    tenant_id: UUID
    step_number: int
    name: Optional[str] = None
    description: Optional[str] = None
    step_type: str
    delay_days: int = 0
    delay_hours: int = 0
    delay_minutes: int = 0
    condition_type: Optional[str] = None
    condition_value: Optional[Dict[str, Any]] = None
    
    # Email content
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    email_template_id: Optional[UUID] = None
    
    # Call script
    call_script: Optional[str] = None
    call_objective: Optional[str] = None
    
    # LinkedIn content
    linkedin_message: Optional[str] = None
    linkedin_connection_note: Optional[str] = None
    
    # AI settings
    use_ai_generation: bool
    ai_prompt_template: Optional[str] = None
    ai_variables: Dict[str, Any] = Field(default_factory=dict)
    
    is_active: bool
    
    # Metrics
    total_sent: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_replied: int = 0
    total_converted: int = 0
    
    # A/B testing
    is_ab_test: bool = False
    ab_variant: Optional[str] = None
    ab_test_group_id: Optional[UUID] = None
    
    created_at: datetime
    updated_at: datetime
    
    # Computed
    total_delay_minutes: Optional[int] = None
    is_email_step: Optional[bool] = None
    is_call_step: Optional[bool] = None
    is_linkedin_step: Optional[bool] = None
    open_rate: Optional[float] = None
    reply_rate: Optional[float] = None


class CampaignSequenceSummary(BaseModel):
    """Summary schema for CampaignSequence."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    step_number: int
    name: Optional[str] = None
    step_type: str
    is_active: bool
    total_sent: int = 0


class CampaignSequenceListResponse(BaseModel):
    """List response for CampaignSequences."""
    
    items: List[CampaignSequenceResponse]
    total: int
