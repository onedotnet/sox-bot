from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.lead import Lead, LeadStatus
from schemas.lead import LeadResponse, LeadUpdate

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("", response_model=list[LeadResponse])
async def list_leads(
    status: str | None = None,
    priority: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead).order_by(desc(Lead.detected_at)).limit(limit).offset(offset)
    if status:
        query = query.where(Lead.status == status)
    if priority:
        query = query.where(Lead.priority == priority)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: int, body: LeadUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if body.status:
        lead.status = LeadStatus(body.status)
        if body.status == "approved":
            lead.reviewed_at = datetime.now(timezone.utc)
    if body.edited_reply is not None:
        lead.edited_reply = body.edited_reply
    await db.commit()
    await db.refresh(lead)
    return lead


@router.post("/{lead_id}/publish")
async def publish_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.status != LeadStatus.approved:
        raise HTTPException(status_code=400, detail="Lead must be approved before publishing")

    from publisher.manager import PublishManager
    manager = PublishManager(db=db)
    success = await manager.publish(lead)
    if not success:
        # Don't 500 — return status so frontend can handle gracefully
        return {"status": "failed", "detail": "Auto-publish unavailable (rate limited or no publisher). Use copy+open."}
    return {"status": "published", "url": lead.published_url}
