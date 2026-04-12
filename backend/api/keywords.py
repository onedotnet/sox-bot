from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.keyword import Keyword
from schemas.keyword import KeywordCreate, KeywordResponse

router = APIRouter(prefix="/api/keywords", tags=["keywords"])


@router.get("", response_model=list[KeywordResponse])
async def list_keywords(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Keyword).order_by(Keyword.id))
    return result.scalars().all()


@router.post("", response_model=KeywordResponse, status_code=201)
async def create_keyword(body: KeywordCreate, db: AsyncSession = Depends(get_db)):
    kw = Keyword(term=body.term, language=body.language, platforms=body.platforms)
    db.add(kw)
    await db.commit()
    await db.refresh(kw)
    return kw


@router.delete("/{keyword_id}", status_code=204)
async def delete_keyword(keyword_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Keyword).where(Keyword.id == keyword_id))
    kw = result.scalar_one_or_none()
    if not kw:
        raise HTTPException(status_code=404, detail="Keyword not found")
    await db.delete(kw)
    await db.commit()
