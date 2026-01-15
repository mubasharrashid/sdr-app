"""API endpoints for Dashboard Statistics."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone

from supabase import create_client, Client

from app.core.config import settings
from app.repositories.dashboard import DashboardRepository
from app.repositories.tenant import TenantRepository
from app.schemas.dashboard import (
    OverviewStats, EmailStats, LeadPipelineStats, ActivityStats,
    CampaignListStats, TrendStats, AgentPerformanceStats, DashboardResponse
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_supabase() -> Client:
    """Get Supabase client."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_dashboard_repo(supabase: Client = Depends(get_supabase)) -> DashboardRepository:
    """Get DashboardRepository instance."""
    return DashboardRepository(supabase)


def get_tenant_repo(supabase: Client = Depends(get_supabase)) -> TenantRepository:
    """Get TenantRepository instance."""
    return TenantRepository(supabase)


# ============================================================================
# Complete Dashboard
# ============================================================================

@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    start_date: Optional[datetime] = Query(None, description="Start date for metrics"),
    end_date: Optional[datetime] = Query(None, description="End date for metrics"),
    include_campaigns: bool = Query(False, description="Include campaign stats"),
    include_trends: bool = Query(False, description="Include trend data"),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """
    Get complete dashboard statistics.
    
    Returns overview, email stats, pipeline, and activity data.
    Optionally includes campaign stats and trends.
    """
    overview = await dashboard_repo.get_overview_stats(tenant_id, start_date, end_date)
    email_stats = await dashboard_repo.get_email_stats(tenant_id, start_date, end_date)
    pipeline = await dashboard_repo.get_pipeline_stats(tenant_id)
    activity = await dashboard_repo.get_activity_stats(tenant_id)
    
    response = DashboardResponse(
        overview=overview,
        email_stats=email_stats,
        pipeline=pipeline,
        activity=activity,
        generated_at=datetime.now(timezone.utc),
        period_start=start_date,
        period_end=end_date
    )
    
    if include_campaigns:
        response.campaigns = await dashboard_repo.get_campaign_stats(tenant_id)
    
    if include_trends:
        trends = []
        for metric in ["emails_sent", "emails_replied", "meetings_booked", "leads_created"]:
            trend = await dashboard_repo.get_trend_stats(metric, tenant_id, days=30)
            trends.append(trend)
        response.trends = trends
    
    return response


# ============================================================================
# Overview Stats
# ============================================================================

@router.get("/overview", response_model=OverviewStats)
async def get_overview_stats(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """
    Get high-level overview statistics.
    
    Includes:
    - Lead counts (total, new, contacted, qualified, converted)
    - Email metrics (sent, opened, clicked, replied, bounced)
    - Call metrics (made, connected, voicemails)
    - Meeting metrics (booked, completed, cancelled)
    - Key rates (open, click, reply, conversion)
    """
    return await dashboard_repo.get_overview_stats(tenant_id, start_date, end_date)


# ============================================================================
# Email Stats
# ============================================================================

@router.get("/emails", response_model=EmailStats)
async def get_email_stats(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """
    Get detailed email statistics.
    
    Includes:
    - Totals (sent, opened, clicked, replied, bounced)
    - Rates (open, click, reply, bounce)
    - Reply breakdown (positive, negative, out of office)
    """
    return await dashboard_repo.get_email_stats(tenant_id, start_date, end_date)


# ============================================================================
# Pipeline Stats
# ============================================================================

@router.get("/pipeline", response_model=LeadPipelineStats)
async def get_pipeline_stats(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """
    Get lead pipeline/funnel statistics.
    
    Includes:
    - Counts by status (new, contacted, engaged, qualified, converted)
    - Counts by source (apollo, linkedin, website, etc.)
    - Conversion rates between stages
    - Visual funnel data
    """
    return await dashboard_repo.get_pipeline_stats(tenant_id)


# ============================================================================
# Activity Stats
# ============================================================================

@router.get("/activity", response_model=ActivityStats)
async def get_activity_stats(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """
    Get activity breakdown statistics.
    
    Includes:
    - Activity counts by type (email, call, meeting, linkedin)
    - Activity counts by channel
    - Daily breakdown for the specified period
    """
    return await dashboard_repo.get_activity_stats(tenant_id, days)


# ============================================================================
# Campaign Stats
# ============================================================================

@router.get("/campaigns", response_model=CampaignListStats)
async def get_campaign_stats(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    campaign_id: Optional[UUID] = Query(None, description="Specific campaign"),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """
    Get campaign performance statistics.
    
    Includes per-campaign:
    - Lead metrics (total, contacted, responded, converted)
    - Email metrics (sent, opened, replied)
    - Call metrics (made, connected)
    - Meeting metrics (booked)
    - Rates (open, reply, conversion)
    """
    return await dashboard_repo.get_campaign_stats(tenant_id, campaign_id)


@router.get("/campaigns/{campaign_id}/sequences")
async def get_sequence_stats(
    campaign_id: UUID,
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """
    Get sequence step performance for a campaign.
    
    Returns performance metrics for each step in the sequence.
    """
    return await dashboard_repo.get_sequence_performance(campaign_id, tenant_id)


# ============================================================================
# Trend Stats
# ============================================================================

@router.get("/trends/{metric}", response_model=TrendStats)
async def get_trend_stats(
    metric: str,
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    days: int = Query(30, ge=7, le=365, description="Number of days"),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """
    Get trend data for a specific metric over time.
    
    Available metrics:
    - emails_sent
    - emails_opened
    - emails_replied
    - calls_made
    - meetings_booked
    - leads_created
    """
    valid_metrics = ["emails_sent", "emails_opened", "emails_replied", 
                     "calls_made", "meetings_booked", "leads_created"]
    
    if metric not in valid_metrics:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid metric. Must be one of: {', '.join(valid_metrics)}"
        )
    
    return await dashboard_repo.get_trend_stats(metric, tenant_id, days)


# ============================================================================
# Agent Performance
# ============================================================================

@router.get("/agents", response_model=List[AgentPerformanceStats])
async def get_agent_performance(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    agent_id: Optional[UUID] = Query(None, description="Specific agent"),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """
    Get AI agent performance statistics.
    
    Includes:
    - Execution counts (total, successful, failed)
    - Average duration
    - Token usage and estimated cost
    - Success rate
    - Task breakdown by type
    """
    return await dashboard_repo.get_agent_performance(tenant_id, agent_id)


# ============================================================================
# Quick Stats (for widgets/cards)
# ============================================================================

@router.get("/quick-stats")
async def get_quick_stats(
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """
    Get quick stats for dashboard cards/widgets.
    
    Returns simplified metrics suitable for display cards.
    """
    overview = await dashboard_repo.get_overview_stats(tenant_id)
    
    return {
        "leads": {
            "total": overview.total_leads,
            "new": overview.new_leads,
            "converted": overview.converted_leads,
            "conversion_rate": overview.conversion_rate
        },
        "emails": {
            "sent": overview.emails_sent,
            "opened": overview.emails_opened,
            "replied": overview.emails_replied,
            "open_rate": overview.open_rate,
            "reply_rate": overview.reply_rate
        },
        "calls": {
            "made": overview.calls_made,
            "connected": overview.calls_connected,
            "connect_rate": overview.call_connect_rate
        },
        "meetings": {
            "booked": overview.meetings_booked,
            "completed": overview.meetings_completed,
            "show_rate": overview.meeting_show_rate
        }
    }


# ============================================================================
# Tenant-Specific Dashboard
# ============================================================================

@router.get("/tenants/{tenant_id}", response_model=DashboardResponse)
async def get_tenant_dashboard(
    tenant_id: UUID,
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    tenant_repo: TenantRepository = Depends(get_tenant_repo),
    dashboard_repo: DashboardRepository = Depends(get_dashboard_repo)
):
    """
    Get complete dashboard for a specific tenant.
    """
    # Verify tenant exists
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    overview = await dashboard_repo.get_overview_stats(tenant_id, start_date, end_date)
    email_stats = await dashboard_repo.get_email_stats(tenant_id, start_date, end_date)
    pipeline = await dashboard_repo.get_pipeline_stats(tenant_id)
    activity = await dashboard_repo.get_activity_stats(tenant_id)
    campaigns = await dashboard_repo.get_campaign_stats(tenant_id)
    
    return DashboardResponse(
        overview=overview,
        email_stats=email_stats,
        pipeline=pipeline,
        activity=activity,
        campaigns=campaigns,
        generated_at=datetime.now(timezone.utc),
        period_start=start_date,
        period_end=end_date
    )
