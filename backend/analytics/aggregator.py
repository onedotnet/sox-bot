from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.content import Content, ContentStatus
from models.knowledge import CommunityMessage
from models.lead import Lead, LeadPriority, LeadStatus


@dataclass
class WeekMetrics:
    # Scout
    leads_discovered: int
    leads_published: int
    enterprise_leads: int
    # Content
    content_generated: int
    content_published: int
    content_cost_cents: int
    # Community
    messages_received: int
    messages_auto_resolved: int
    messages_escalated: int
    community_leads: int
    resolution_rate: float


class AnalyticsAggregator:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def aggregate_week(self, week_start: datetime, week_end: datetime) -> WeekMetrics:
        # Scout metrics
        leads_discovered = await self._count(Lead, Lead.detected_at, week_start, week_end)
        leads_published = await self._count(
            Lead, Lead.detected_at, week_start, week_end,
            Lead.status == LeadStatus.published,
        )
        enterprise_leads = await self._count(
            Lead, Lead.detected_at, week_start, week_end,
            Lead.priority == LeadPriority.high,
        )

        # Content metrics
        content_generated = await self._count(Content, Content.created_at, week_start, week_end)
        content_published = await self._count(
            Content, Content.created_at, week_start, week_end,
            Content.status == ContentStatus.published,
        )
        cost_result = await self.db.execute(
            select(func.coalesce(func.sum(Content.generation_cost_cents), 0)).where(
                and_(Content.created_at >= week_start, Content.created_at < week_end)
            )
        )
        content_cost_cents = cost_result.scalar() or 0

        # Community metrics
        messages_received = await self._count(
            CommunityMessage, CommunityMessage.created_at, week_start, week_end
        )
        messages_escalated = await self._count(
            CommunityMessage, CommunityMessage.created_at, week_start, week_end,
            CommunityMessage.escalated == True,  # noqa: E712
        )
        messages_auto_resolved = messages_received - messages_escalated
        community_leads = await self._count(
            CommunityMessage, CommunityMessage.created_at, week_start, week_end,
            CommunityMessage.is_lead == True,  # noqa: E712
        )
        resolution_rate = (
            (messages_auto_resolved / messages_received * 100) if messages_received > 0 else 0.0
        )

        return WeekMetrics(
            leads_discovered=leads_discovered,
            leads_published=leads_published,
            enterprise_leads=enterprise_leads,
            content_generated=content_generated,
            content_published=content_published,
            content_cost_cents=content_cost_cents,
            messages_received=messages_received,
            messages_auto_resolved=messages_auto_resolved,
            messages_escalated=messages_escalated,
            community_leads=community_leads,
            resolution_rate=round(resolution_rate, 1),
        )

    async def _count(self, model, date_col, start: datetime, end: datetime, *extra_filters):
        query = select(func.count(model.id)).where(and_(date_col >= start, date_col < end))
        for f in extra_filters:
            query = query.where(f)
        result = await self.db.execute(query)
        return result.scalar() or 0
