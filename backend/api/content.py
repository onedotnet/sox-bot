from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.content import Content, ContentStatus, ContentType
from schemas.content import ContentGenerateRequest, ContentResponse, ContentUpdate

router = APIRouter(prefix="/api/content", tags=["content"])


@router.get("", response_model=list[ContentResponse])
async def list_content(
    status: ContentStatus | None = Query(None),
    content_type: ContentType | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Content).order_by(Content.id.desc()).offset(offset).limit(limit)
    if status is not None:
        stmt = stmt.where(Content.status == status)
    if content_type is not None:
        stmt = stmt.where(Content.content_type == content_type)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content


@router.patch("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: int,
    body: ContentUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(content, field, value)

    await db.commit()
    await db.refresh(content)
    return content


@router.post("/generate", status_code=202)
async def trigger_generate(body: ContentGenerateRequest):
    from tasks.celery_app import generate_content_task

    task = generate_content_task.delay(
        keyword=body.seo_keyword,
        content_type=body.content_type.value,
        language=body.language.value,
        target_platform=body.target_platform,
        generate_translation=body.generate_translation,
    )
    return {"task_id": task.id, "status": "queued"}


@router.post("/{content_id}/publish")
async def publish_content(content_id: int, db: AsyncSession = Depends(get_db)):
    """Publish content to its target platform (blog → MDX file + git push)."""
    from datetime import datetime, timezone
    import json

    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    if content.target_platform == "blog":
        from publisher.platforms.blog import BlogPublisher
        publisher = BlogPublisher()
        tags = []
        try:
            tags = json.loads(content.seo_tags) if content.seo_tags else []
        except (json.JSONDecodeError, TypeError):
            pass
        url = await publisher.publish(
            title=content.title,
            body=content.body,
            summary=content.summary or "",
            tags=tags,
            language=content.language.value,
        )
        if url:
            content.status = ContentStatus.published
            content.published_url = url
            content.published_at = datetime.now(timezone.utc)
            await db.commit()
            return {"status": "published", "url": url}
        return {"status": "failed", "detail": "Blog publish failed"}
    else:
        return {"status": "failed", "detail": f"Publishing to {content.target_platform} not yet supported. Copy content manually."}
