from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.lead import Lead, LeadStatus, LeadPriority

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    total = await db.execute(select(func.count(Lead.id)))
    pending = await db.execute(
        select(func.count(Lead.id)).where(Lead.status == LeadStatus.pending_review)
    )
    published = await db.execute(
        select(func.count(Lead.id)).where(Lead.status == LeadStatus.published)
    )
    enterprise = await db.execute(
        select(func.count(Lead.id)).where(Lead.priority == LeadPriority.high)
    )
    return {
        "total_leads": total.scalar() or 0,
        "pending_review": pending.scalar() or 0,
        "published": published.scalar() or 0,
        "enterprise_leads": enterprise.scalar() or 0,
    }
