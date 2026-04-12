from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.analytics import WeeklyReport
from models.content import Content, ContentStatus
from models.knowledge import CommunityMessage
from models.lead import Lead, LeadStatus
from schemas.analytics import AnalyticsOverview, WeeklyReportResponse

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/reports", response_model=list[WeeklyReportResponse])
async def list_reports(limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WeeklyReport).order_by(desc(WeeklyReport.week_start)).limit(limit)
    )
    return result.scalars().all()


@router.get("/overview", response_model=AnalyticsOverview)
async def get_overview(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())  # This Monday
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    prev_week_start = week_start - timedelta(days=7)

    # Live counts
    scout_pending = (
        await db.execute(
            select(func.count(Lead.id)).where(Lead.status == LeadStatus.pending_review)
        )
    ).scalar() or 0

    scout_published = (
        await db.execute(
            select(func.count(Lead.id)).where(
                and_(
                    Lead.status == LeadStatus.published,
                    Lead.published_at >= week_start,
                )
            )
        )
    ).scalar() or 0

    content_drafts = (
        await db.execute(
            select(func.count(Content.id)).where(Content.status == ContentStatus.draft)
        )
    ).scalar() or 0

    content_scheduled = (
        await db.execute(
            select(func.count(Content.id)).where(Content.status == ContentStatus.scheduled)
        )
    ).scalar() or 0

    msgs_today = (
        await db.execute(
            select(func.count(CommunityMessage.id)).where(
                CommunityMessage.created_at >= today_start
            )
        )
    ).scalar() or 0

    total_msgs = (
        await db.execute(select(func.count(CommunityMessage.id)))
    ).scalar() or 0
    escalated_msgs = (
        await db.execute(
            select(func.count(CommunityMessage.id)).where(
                CommunityMessage.escalated == True  # noqa: E712
            )
        )
    ).scalar() or 0
    res_rate = (
        ((total_msgs - escalated_msgs) / total_msgs * 100) if total_msgs > 0 else 0.0
    )

    # Trends (vs last week)
    this_week_leads = (
        await db.execute(
            select(func.count(Lead.id)).where(Lead.detected_at >= week_start)
        )
    ).scalar() or 0
    last_week_leads = (
        await db.execute(
            select(func.count(Lead.id)).where(
                and_(Lead.detected_at >= prev_week_start, Lead.detected_at < week_start)
            )
        )
    ).scalar() or 0

    this_week_content = (
        await db.execute(
            select(func.count(Content.id)).where(Content.created_at >= week_start)
        )
    ).scalar() or 0
    last_week_content = (
        await db.execute(
            select(func.count(Content.id)).where(
                and_(Content.created_at >= prev_week_start, Content.created_at < week_start)
            )
        )
    ).scalar() or 0

    this_week_msgs = (
        await db.execute(
            select(func.count(CommunityMessage.id)).where(
                CommunityMessage.created_at >= week_start
            )
        )
    ).scalar() or 0
    last_week_msgs = (
        await db.execute(
            select(func.count(CommunityMessage.id)).where(
                and_(
                    CommunityMessage.created_at >= prev_week_start,
                    CommunityMessage.created_at < week_start,
                )
            )
        )
    ).scalar() or 0

    def pct_change(curr: int, prev: int) -> float:
        if prev == 0:
            return 100.0 if curr > 0 else 0.0
        return round((curr - prev) / prev * 100, 1)

    return AnalyticsOverview(
        scout_pending=scout_pending,
        scout_published_this_week=scout_published,
        content_drafts=content_drafts,
        content_scheduled=content_scheduled,
        community_messages_today=msgs_today,
        community_resolution_rate=round(res_rate, 1),
        leads_trend=pct_change(this_week_leads, last_week_leads),
        content_trend=pct_change(this_week_content, last_week_content),
        messages_trend=pct_change(this_week_msgs, last_week_msgs),
    )


@router.post("/reports/generate", status_code=202)
async def trigger_report():
    from tasks.celery_app import generate_weekly_report_task

    generate_weekly_report_task.delay()
    return {"status": "queued", "message": "Weekly report generation started"}
