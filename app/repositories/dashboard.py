"""Repository for Dashboard Statistics."""
from typing import Optional, Dict, List, Any
from uuid import UUID
from datetime import datetime, timedelta, timezone, date

from app.schemas.dashboard import (
    OverviewStats, EmailStats, LeadPipelineStats, ActivityStats,
    CampaignStats, CampaignListStats, TrendDataPoint, TrendStats,
    AgentPerformanceStats
)


class DashboardRepository:
    """Repository for aggregating dashboard statistics."""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
    
    async def get_overview_stats(
        self, 
        tenant_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> OverviewStats:
        """Get high-level overview statistics."""
        stats = OverviewStats()
        
        # Build base query filters
        def apply_filters(query, table_has_tenant=True):
            if tenant_id and table_has_tenant:
                query = query.eq("tenant_id", str(tenant_id))
            if start_date:
                query = query.gte("created_at", start_date.isoformat())
            if end_date:
                query = query.lte("created_at", end_date.isoformat())
            return query
        
        # Lead stats from leads table
        leads_query = self.client.table("leads").select("status, emails_sent, emails_opened, emails_clicked, emails_replied, emails_bounced, calls_made, calls_connected, voicemails_left, meetings_booked, meetings_completed")
        leads_query = apply_filters(leads_query)
        leads_result = leads_query.execute()
        
        if leads_result.data:
            for lead in leads_result.data:
                stats.total_leads += 1
                status = lead.get("status", "new")
                
                if status == "new":
                    stats.new_leads += 1
                elif status in ("contacted", "in_progress"):
                    stats.contacted_leads += 1
                elif status == "qualified":
                    stats.qualified_leads += 1
                elif status == "converted":
                    stats.converted_leads += 1
                
                # Aggregate email stats
                stats.emails_sent += lead.get("emails_sent", 0) or 0
                stats.emails_opened += lead.get("emails_opened", 0) or 0
                stats.emails_clicked += lead.get("emails_clicked", 0) or 0
                stats.emails_replied += lead.get("emails_replied", 0) or 0
                stats.emails_bounced += lead.get("emails_bounced", 0) or 0
                
                # Aggregate call stats
                stats.calls_made += lead.get("calls_made", 0) or 0
                stats.calls_connected += lead.get("calls_connected", 0) or 0
                stats.voicemails_left += lead.get("voicemails_left", 0) or 0
                
                # Aggregate meeting stats
                stats.meetings_booked += lead.get("meetings_booked", 0) or 0
                stats.meetings_completed += lead.get("meetings_completed", 0) or 0
        
        # Get meetings cancelled from meetings table
        meetings_query = self.client.table("meetings").select("status", count="exact").eq("status", "cancelled")
        meetings_query = apply_filters(meetings_query)
        meetings_result = meetings_query.execute()
        stats.meetings_cancelled = meetings_result.count or 0
        
        # Calculate rates
        if stats.emails_sent > 0:
            stats.open_rate = round((stats.emails_opened / stats.emails_sent) * 100, 2)
            stats.click_rate = round((stats.emails_clicked / stats.emails_sent) * 100, 2)
            stats.reply_rate = round((stats.emails_replied / stats.emails_sent) * 100, 2)
        
        if stats.total_leads > 0:
            stats.conversion_rate = round((stats.converted_leads / stats.total_leads) * 100, 2)
        
        if stats.calls_made > 0:
            stats.call_connect_rate = round((stats.calls_connected / stats.calls_made) * 100, 2)
        
        if stats.meetings_booked > 0:
            stats.meeting_show_rate = round((stats.meetings_completed / stats.meetings_booked) * 100, 2)
        
        return stats
    
    async def get_email_stats(
        self,
        tenant_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> EmailStats:
        """Get detailed email statistics."""
        stats = EmailStats()
        
        # Get from leads aggregate
        leads_query = self.client.table("leads").select("emails_sent, emails_opened, emails_clicked, emails_replied, emails_bounced")
        if tenant_id:
            leads_query = leads_query.eq("tenant_id", str(tenant_id))
        leads_result = leads_query.execute()
        
        for lead in leads_result.data:
            stats.total_sent += lead.get("emails_sent", 0) or 0
            stats.total_opened += lead.get("emails_opened", 0) or 0
            stats.total_clicked += lead.get("emails_clicked", 0) or 0
            stats.total_replied += lead.get("emails_replied", 0) or 0
            stats.total_bounced += lead.get("emails_bounced", 0) or 0
        
        # Get reply breakdown from email_replies table
        replies_query = self.client.table("email_replies").select("reply_type, sentiment, is_out_of_office")
        if tenant_id:
            replies_query = replies_query.eq("tenant_id", str(tenant_id))
        if start_date:
            replies_query = replies_query.gte("received_at", start_date.isoformat())
        if end_date:
            replies_query = replies_query.lte("received_at", end_date.isoformat())
        replies_result = replies_query.execute()
        
        for reply in replies_result.data:
            if reply.get("is_out_of_office"):
                stats.out_of_office_replies += 1
            elif reply.get("sentiment") == "positive" or reply.get("reply_type") == "interested":
                stats.positive_replies += 1
            elif reply.get("sentiment") == "negative" or reply.get("reply_type") == "not_interested":
                stats.negative_replies += 1
        
        # Calculate rates
        if stats.total_sent > 0:
            stats.open_rate = round((stats.total_opened / stats.total_sent) * 100, 2)
            stats.click_rate = round((stats.total_clicked / stats.total_sent) * 100, 2)
            stats.reply_rate = round((stats.total_replied / stats.total_sent) * 100, 2)
            stats.bounce_rate = round((stats.total_bounced / stats.total_sent) * 100, 2)
        
        return stats
    
    async def get_pipeline_stats(
        self,
        tenant_id: Optional[UUID] = None
    ) -> LeadPipelineStats:
        """Get lead pipeline/funnel statistics."""
        stats = LeadPipelineStats()
        
        leads_query = self.client.table("leads").select("status, source, outreach_status")
        if tenant_id:
            leads_query = leads_query.eq("tenant_id", str(tenant_id))
        leads_result = leads_query.execute()
        
        source_counts: Dict[str, int] = {}
        
        for lead in leads_result.data:
            stats.total += 1
            status = lead.get("status") or lead.get("outreach_status") or "new"
            source = lead.get("source") or "unknown"
            
            # Count by status
            if status == "new":
                stats.new += 1
            elif status in ("contacted", "in_progress"):
                stats.contacted += 1
            elif status == "engaged":
                stats.engaged += 1
            elif status == "qualified":
                stats.qualified += 1
            elif status == "converted":
                stats.converted += 1
            elif status == "unqualified":
                stats.unqualified += 1
            elif status == "do_not_contact":
                stats.do_not_contact += 1
            
            # Count by source
            source_counts[source] = source_counts.get(source, 0) + 1
        
        stats.by_source = source_counts
        
        # Calculate conversion rates
        if stats.total > 0:
            stats.contact_rate = round((stats.contacted / stats.total) * 100, 2)
        if stats.contacted > 0:
            stats.engagement_rate = round((stats.engaged / stats.contacted) * 100, 2)
        if stats.engaged > 0:
            stats.qualification_rate = round((stats.qualified / stats.engaged) * 100, 2)
        if stats.qualified > 0:
            stats.conversion_rate = round((stats.converted / stats.qualified) * 100, 2)
        
        # Build funnel
        stats.funnel = [
            {"stage": "Total Leads", "count": stats.total, "percent": 100},
            {"stage": "Contacted", "count": stats.contacted, "percent": round((stats.contacted / stats.total) * 100, 1) if stats.total > 0 else 0},
            {"stage": "Engaged", "count": stats.engaged, "percent": round((stats.engaged / stats.total) * 100, 1) if stats.total > 0 else 0},
            {"stage": "Qualified", "count": stats.qualified, "percent": round((stats.qualified / stats.total) * 100, 1) if stats.total > 0 else 0},
            {"stage": "Converted", "count": stats.converted, "percent": round((stats.converted / stats.total) * 100, 1) if stats.total > 0 else 0},
        ]
        
        return stats
    
    async def get_activity_stats(
        self,
        tenant_id: Optional[UUID] = None,
        days: int = 7
    ) -> ActivityStats:
        """Get activity breakdown statistics."""
        stats = ActivityStats()
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Get from outreach_activity_logs
        query = self.client.table("outreach_activity_logs").select("activity_type, action_type, channel, activity_at, performed_at, created_at")
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        query = query.gte("created_at", start_date.isoformat())
        result = query.execute()
        
        channel_counts: Dict[str, int] = {}
        daily_counts: Dict[str, Dict[str, int]] = {}
        
        for activity in result.data:
            stats.total_activities += 1
            
            # Get activity type (use activity_type or fall back to action_type)
            activity_type = activity.get("activity_type") or activity.get("action_type") or "unknown"
            channel = activity.get("channel") or "email"
            
            # Count by type
            if activity_type == "email_sent":
                stats.emails_sent += 1
            elif activity_type == "email_opened":
                stats.emails_opened += 1
            elif activity_type == "email_clicked":
                stats.emails_clicked += 1
            elif activity_type == "email_replied":
                stats.emails_replied += 1
            elif activity_type in ("call_made", "call"):
                stats.calls_made += 1
            elif activity_type == "call_connected":
                stats.calls_connected += 1
            elif activity_type == "meeting_booked":
                stats.meetings_booked += 1
            elif activity_type in ("linkedin_sent", "linkedin_message"):
                stats.linkedin_sent += 1
            
            # Count by channel
            channel_counts[channel] = channel_counts.get(channel, 0) + 1
            
            # Count by day
            activity_date = activity.get("activity_at") or activity.get("performed_at") or activity.get("created_at")
            if activity_date:
                day_key = activity_date[:10]  # YYYY-MM-DD
                if day_key not in daily_counts:
                    daily_counts[day_key] = {}
                daily_counts[day_key][activity_type] = daily_counts[day_key].get(activity_type, 0) + 1
        
        stats.by_channel = channel_counts
        
        # Build daily breakdown
        for day, counts in sorted(daily_counts.items()):
            stats.daily_breakdown.append({
                "date": day,
                "total": sum(counts.values()),
                **counts
            })
        
        return stats
    
    async def get_campaign_stats(
        self,
        tenant_id: Optional[UUID] = None,
        campaign_id: Optional[UUID] = None
    ) -> CampaignListStats:
        """Get campaign performance statistics."""
        result = CampaignListStats()
        
        query = self.client.table("campaigns").select("*")
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        if campaign_id:
            query = query.eq("id", str(campaign_id))
        campaigns_result = query.execute()
        
        for campaign in campaigns_result.data:
            stats = CampaignStats(
                campaign_id=campaign.get("id"),
                campaign_name=campaign.get("name", "Unnamed"),
                status=campaign.get("status", "draft"),
                total_leads=campaign.get("total_leads", 0) or 0,
                leads_contacted=campaign.get("leads_contacted", 0) or 0,
                leads_responded=campaign.get("leads_responded", 0) or 0,
                leads_converted=campaign.get("leads_converted", 0) or 0,
                emails_sent=campaign.get("emails_sent", 0) or 0,
                emails_opened=campaign.get("emails_opened", 0) or 0,
                emails_replied=campaign.get("emails_replied", 0) or 0,
                calls_made=campaign.get("calls_made", 0) or 0,
                calls_connected=campaign.get("calls_connected", 0) or 0,
                meetings_booked=campaign.get("meetings_booked", 0) or 0
            )
            
            # Calculate rates
            if stats.emails_sent > 0:
                stats.open_rate = round((stats.emails_opened / stats.emails_sent) * 100, 2)
                stats.reply_rate = round((stats.emails_replied / stats.emails_sent) * 100, 2)
            if stats.total_leads > 0:
                stats.conversion_rate = round((stats.leads_converted / stats.total_leads) * 100, 2)
            
            result.campaigns.append(stats)
            result.total_campaigns += 1
            if campaign.get("status") == "active":
                result.active_campaigns += 1
        
        return result
    
    async def get_trend_stats(
        self,
        metric: str,
        tenant_id: Optional[UUID] = None,
        days: int = 30
    ) -> TrendStats:
        """Get trend data for a specific metric."""
        trend = TrendStats(period="daily", metric=metric)
        
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Map metric to table and field
        metric_config = {
            "emails_sent": ("outreach_activity_logs", "activity_type", "email_sent"),
            "emails_opened": ("outreach_activity_logs", "activity_type", "email_opened"),
            "emails_replied": ("outreach_activity_logs", "activity_type", "email_replied"),
            "calls_made": ("outreach_activity_logs", "activity_type", "call_made"),
            "meetings_booked": ("outreach_activity_logs", "activity_type", "meeting_booked"),
            "leads_created": ("leads", None, None),
        }
        
        if metric not in metric_config:
            return trend
        
        table, filter_field, filter_value = metric_config[metric]
        
        query = self.client.table(table).select("created_at")
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        query = query.gte("created_at", start_date.isoformat())
        if filter_field and filter_value:
            query = query.eq(filter_field, filter_value)
        result = query.execute()
        
        # Group by day
        daily_counts: Dict[str, int] = {}
        for row in result.data:
            day = row.get("created_at", "")[:10]
            daily_counts[day] = daily_counts.get(day, 0) + 1
        
        # Fill in missing days with 0
        current_date = start_date.date()
        end_date = datetime.now(timezone.utc).date()
        while current_date <= end_date:
            day_str = current_date.isoformat()
            count = daily_counts.get(day_str, 0)
            trend.data_points.append(TrendDataPoint(date=current_date, value=count))
            trend.total += count
            current_date += timedelta(days=1)
        
        if trend.data_points:
            trend.average = round(trend.total / len(trend.data_points), 2)
        
        return trend
    
    async def get_agent_performance(
        self,
        tenant_id: Optional[UUID] = None,
        agent_id: Optional[UUID] = None
    ) -> List[AgentPerformanceStats]:
        """Get AI agent performance statistics."""
        results = []
        
        # Get agent executions
        query = self.client.table("agent_executions").select("agent_id, status, duration_ms, total_tokens, estimated_cost, task_type")
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        if agent_id:
            query = query.eq("agent_id", str(agent_id))
        executions_result = query.execute()
        
        # Group by agent
        agent_stats: Dict[str, Dict] = {}
        for exec in executions_result.data:
            aid = exec.get("agent_id")
            if not aid:
                continue
            
            if aid not in agent_stats:
                agent_stats[aid] = {
                    "total": 0, "success": 0, "failed": 0,
                    "duration_sum": 0, "tokens": 0, "cost": 0,
                    "tasks": {}
                }
            
            agent_stats[aid]["total"] += 1
            if exec.get("status") == "completed":
                agent_stats[aid]["success"] += 1
            elif exec.get("status") == "failed":
                agent_stats[aid]["failed"] += 1
            
            agent_stats[aid]["duration_sum"] += exec.get("duration_ms", 0) or 0
            agent_stats[aid]["tokens"] += exec.get("total_tokens", 0) or 0
            agent_stats[aid]["cost"] += float(exec.get("estimated_cost", 0) or 0)
            
            task_type = exec.get("task_type", "unknown")
            agent_stats[aid]["tasks"][task_type] = agent_stats[aid]["tasks"].get(task_type, 0) + 1
        
        # Get agent names
        if agent_stats:
            agents_query = self.client.table("agents").select("id, name").in_("id", list(agent_stats.keys()))
            agents_result = agents_query.execute()
            agent_names = {a["id"]: a["name"] for a in agents_result.data}
        else:
            agent_names = {}
        
        # Build results
        for aid, data in agent_stats.items():
            stats = AgentPerformanceStats(
                agent_id=aid,
                agent_name=agent_names.get(aid, "Unknown Agent"),
                total_executions=data["total"],
                successful_executions=data["success"],
                failed_executions=data["failed"],
                total_tokens_used=data["tokens"],
                estimated_cost=round(data["cost"], 4),
                tasks_by_type=data["tasks"]
            )
            
            if data["total"] > 0:
                stats.success_rate = round((data["success"] / data["total"]) * 100, 2)
                stats.avg_duration_ms = round(data["duration_sum"] / data["total"], 2)
            
            results.append(stats)
        
        return results
    
    async def get_sequence_performance(
        self,
        campaign_id: UUID,
        tenant_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get sequence step performance for a campaign."""
        query = self.client.table("campaign_sequences").select("*").eq("campaign_id", str(campaign_id)).order("step_number")
        if tenant_id:
            query = query.eq("tenant_id", str(tenant_id))
        result = query.execute()
        
        steps = []
        for step in result.data:
            total_sent = step.get("total_sent", 0) or 0
            total_opened = step.get("total_opened", 0) or 0
            total_replied = step.get("total_replied", 0) or 0
            
            steps.append({
                "step_number": step.get("step_number"),
                "step_name": step.get("name"),
                "step_type": step.get("step_type"),
                "total_sent": total_sent,
                "total_opened": total_opened,
                "total_clicked": step.get("total_clicked", 0) or 0,
                "total_replied": total_replied,
                "open_rate": round((total_opened / total_sent) * 100, 2) if total_sent > 0 else 0,
                "reply_rate": round((total_replied / total_sent) * 100, 2) if total_sent > 0 else 0
            })
        
        return steps
