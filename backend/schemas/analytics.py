from datetime import datetime

from pydantic import BaseModel


class WeeklyReportResponse(BaseModel):
    id: int
    week_start: datetime
    week_end: datetime
    leads_discovered: int
    leads_published: int
    enterprise_leads: int
    content_generated: int
    content_published: int
    content_cost_cents: int
    messages_received: int
    messages_auto_resolved: int
    messages_escalated: int
    community_leads: int
    resolution_rate: float
    summary: str
    action_items: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalyticsOverview(BaseModel):
    # Current week (live)
    scout_pending: int
    scout_published_this_week: int
    content_drafts: int
    content_scheduled: int
    community_messages_today: int
    community_resolution_rate: float
    # Trends (vs last week)
    leads_trend: float  # percentage change
    content_trend: float
    messages_trend: float
