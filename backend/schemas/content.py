from datetime import datetime

from pydantic import BaseModel

from models.content import ContentLanguage, ContentStatus, ContentType


class ContentResponse(BaseModel):
    id: int
    title: str
    body: str
    summary: str | None
    content_type: ContentType
    language: ContentLanguage
    status: ContentStatus
    seo_keyword: str | None
    seo_tags: str | None
    outline_model: str | None
    body_model: str | None
    translate_model: str | None
    generation_cost_cents: int
    target_platform: str
    published_url: str | None
    scheduled_at: datetime | None
    published_at: datetime | None
    quality_passed: bool
    quality_notes: str | None
    pair_id: str | None
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class ContentUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    status: ContentStatus | None = None
    scheduled_at: datetime | None = None


class ContentGenerateRequest(BaseModel):
    content_type: ContentType
    seo_keyword: str
    language: ContentLanguage
    target_platform: str
    generate_translation: bool = False
