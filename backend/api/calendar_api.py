from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.content import Content
from schemas.content import ContentResponse

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("", response_model=list[ContentResponse])
async def get_calendar(
    week_start: str = Query(..., description="ISO date string, e.g. 2026-04-13"),
    db: AsyncSession = Depends(get_db),
):
    try:
        start_dt = datetime.fromisoformat(week_start).replace(tzinfo=timezone.utc)
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid week_start date format. Use YYYY-MM-DD.")

    from datetime import timedelta
    end_dt = start_dt + timedelta(days=7)

    result = await db.execute(
        select(Content)
        .where(Content.scheduled_at >= start_dt)
        .where(Content.scheduled_at < end_dt)
        .order_by(Content.scheduled_at)
    )
    return result.scalars().all()
