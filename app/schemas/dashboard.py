"""Pydantic schemas for Dashboard Statistics."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class OverviewStats(BaseModel):
    """High-level overview statistics."""
    
    # Lead stats
    total_leads: int = 0
    new_leads: int = 0
    contacted_leads: int = 0
    qualified_leads: int = 0
    converted_leads: int = 0
    
    # Email stats
    emails_sent: int = 0
    emails_opened: int = 0
    emails_clicked: int = 0
    emails_replied: int = 0
    emails_bounced: int = 0
    
    # Call stats
    calls_made: int = 0
    calls_connected: int = 0
    voicemails_left: int = 0
    
    # Meeting stats
    meetings_booked: int = 0
    meetings_completed: int = 0
    meetings_cancelled: int = 0
    
    # Rates
    open_rate: float = 0.0
    click_rate: float = 0.0
    reply_rate: float = 0.0
    conversion_rate: float = 0.0
    call_connect_rate: float = 0.0
    meeting_show_rate: float = 0.0


class EmailStats(BaseModel):
    """Email performance statistics."""
    
    total_sent: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_replied: int = 0
    total_bounced: int = 0
    
    unique_opens: int = 0
    unique_clicks: int = 0
    
    open_rate: float = 0.0
    click_rate: float = 0.0
    reply_rate: float = 0.0
    bounce_rate: float = 0.0
    
    # Response breakdown
    positive_replies: int = 0
    negative_replies: int = 0
    out_of_office_replies: int = 0
    
    avg_response_time_hours: Optional[float] = None


class LeadPipelineStats(BaseModel):
    """Lead pipeline/funnel statistics."""
    
    total: int = 0
    
    # By status
    new: int = 0
    contacted: int = 0
    engaged: int = 0
    qualified: int = 0
    converted: int = 0
    unqualified: int = 0
    do_not_contact: int = 0
    
    # By source
    by_source: Dict[str, int] = Field(default_factory=dict)
    
    # Conversion rates
    contact_rate: float = 0.0  # contacted / total
    engagement_rate: float = 0.0  # engaged / contacted
    qualification_rate: float = 0.0  # qualified / engaged
    conversion_rate: float = 0.0  # converted / qualified
    
    # Funnel
    funnel: List[Dict[str, Any]] = Field(default_factory=list)


class ActivityStats(BaseModel):
    """Activity breakdown statistics."""
    
    total_activities: int = 0
    
    # By type
    emails_sent: int = 0
    emails_opened: int = 0
    emails_clicked: int = 0
    emails_replied: int = 0
    calls_made: int = 0
    calls_connected: int = 0
    meetings_booked: int = 0
    linkedin_sent: int = 0
    
    # By channel
    by_channel: Dict[str, int] = Field(default_factory=dict)
    
    # By day (last 7 days)
    daily_breakdown: List[Dict[str, Any]] = Field(default_factory=list)


class CampaignStats(BaseModel):
    """Campaign performance statistics."""
    
    campaign_id: str
    campaign_name: str
    status: str
    
    total_leads: int = 0
    leads_contacted: int = 0
    leads_responded: int = 0
    leads_converted: int = 0
    
    emails_sent: int = 0
    emails_opened: int = 0
    emails_replied: int = 0
    
    calls_made: int = 0
    calls_connected: int = 0
    
    meetings_booked: int = 0
    
    open_rate: float = 0.0
    reply_rate: float = 0.0
    conversion_rate: float = 0.0


class CampaignListStats(BaseModel):
    """List of campaign statistics."""
    
    campaigns: List[CampaignStats] = Field(default_factory=list)
    total_campaigns: int = 0
    active_campaigns: int = 0


class SequenceStepStats(BaseModel):
    """Sequence step performance."""
    
    step_number: int
    step_name: Optional[str] = None
    step_type: str
    
    total_sent: int = 0
    total_opened: int = 0
    total_clicked: int = 0
    total_replied: int = 0
    
    open_rate: float = 0.0
    reply_rate: float = 0.0
    drop_off_rate: float = 0.0


class TrendDataPoint(BaseModel):
    """Single data point for trends."""
    
    date: date
    value: int = 0
    label: Optional[str] = None


class TrendStats(BaseModel):
    """Time-based trend statistics."""
    
    period: str  # daily, weekly, monthly
    metric: str  # emails_sent, replies, meetings, etc.
    
    data_points: List[TrendDataPoint] = Field(default_factory=list)
    
    total: int = 0
    average: float = 0.0
    change_percent: Optional[float] = None  # vs previous period


class AgentPerformanceStats(BaseModel):
    """AI Agent performance statistics."""
    
    agent_id: str
    agent_name: str
    
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    
    avg_duration_ms: Optional[float] = None
    total_tokens_used: int = 0
    estimated_cost: float = 0.0
    
    success_rate: float = 0.0
    
    # Task breakdown
    tasks_by_type: Dict[str, int] = Field(default_factory=dict)


class DashboardResponse(BaseModel):
    """Complete dashboard response."""
    
    overview: OverviewStats
    email_stats: EmailStats
    pipeline: LeadPipelineStats
    activity: ActivityStats
    
    # Optional detailed stats
    campaigns: Optional[CampaignListStats] = None
    trends: Optional[List[TrendStats]] = None
    
    # Metadata
    generated_at: datetime
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
