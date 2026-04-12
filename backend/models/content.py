import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from models.lead import Base


class ContentType(str, enum.Enum):
    seo_article = "seo_article"
    industry_brief = "industry_brief"
    tutorial = "tutorial"
    comparison = "comparison"
    changelog = "changelog"
    social_post = "social_post"


class ContentLanguage(str, enum.Enum):
    en = "en"
    zh = "zh"


class ContentStatus(str, enum.Enum):
    draft = "draft"
    review = "review"
    approved = "approved"
    scheduled = "scheduled"
    published = "published"
    rejected = "rejected"


class Content(Base):
    __tablename__ = "contents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType))
    language: Mapped[ContentLanguage] = mapped_column(Enum(ContentLanguage))
    status: Mapped[ContentStatus] = mapped_column(Enum(ContentStatus), default=ContentStatus.draft)

    seo_keyword: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_tags: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array stored as text

    outline_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    body_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    translate_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    generation_cost_cents: Mapped[int] = mapped_column(Integer, default=0)

    target_platform: Mapped[str] = mapped_column(String(50))
    published_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    quality_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    quality_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    pair_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
