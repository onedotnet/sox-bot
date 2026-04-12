from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.knowledge import CommunityMessage, KnowledgeChunk
from schemas.community import MessageResponse, KnowledgeChunkResponse, CommunityStats

router = APIRouter(prefix="/api/community", tags=["community"])


@router.get("/messages", response_model=list[MessageResponse])
async def list_messages(
    escalated: bool | None = None,
    is_lead: bool | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(CommunityMessage).order_by(desc(CommunityMessage.created_at)).limit(limit)
    if escalated is not None:
        query = query.where(CommunityMessage.escalated == escalated)
    if is_lead is not None:
        query = query.where(CommunityMessage.is_lead == is_lead)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats", response_model=CommunityStats)
async def get_community_stats(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(CommunityMessage.id)))).scalar() or 0
    escalated = (
        await db.execute(
            select(func.count(CommunityMessage.id)).where(CommunityMessage.escalated == True)  # noqa: E712
        )
    ).scalar() or 0
    leads = (
        await db.execute(
            select(func.count(CommunityMessage.id)).where(CommunityMessage.is_lead == True)  # noqa: E712
        )
    ).scalar() or 0
    auto_resolved = total - escalated
    rate = (auto_resolved / total * 100) if total > 0 else 0.0
    return CommunityStats(
        total_messages=total,
        auto_resolved=auto_resolved,
        escalated=escalated,
        leads_detected=leads,
        resolution_rate=round(rate, 1),
    )


@router.get("/knowledge", response_model=list[KnowledgeChunkResponse])
async def list_knowledge(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeChunk)
        .order_by(KnowledgeChunk.source_file, KnowledgeChunk.chunk_index)
        .limit(limit)
    )
    return result.scalars().all()


@router.post("/knowledge/reindex", status_code=202)
async def trigger_reindex():
    from tasks.celery_app import reindex_knowledge_task

    reindex_knowledge_task.delay()
    return {"status": "queued", "message": "Knowledge base reindexing started"}
