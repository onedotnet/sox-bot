import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class LeadStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"
    published = "published"
    dismissed = "dismissed"


class LeadIntent(str, enum.Enum):
    help_seeking = "help_seeking"
    complaint = "complaint"
    comparison = "comparison"
    technical = "technical"
    enterprise = "enterprise"


class LeadPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source: Mapped[str] = mapped_column(String(50))
    source_id: Mapped[str] = mapped_column(String(255), unique=True)
    source_url: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(String(255))
    original_text: Mapped[str] = mapped_column(Text)
    subreddit: Mapped[str | None] = mapped_column(String(100))

    relevance_score: Mapped[int] = mapped_column(Integer)
    intent: Mapped[LeadIntent] = mapped_column(Enum(LeadIntent))
    sentiment: Mapped[str] = mapped_column(String(50))
    priority: Mapped[LeadPriority] = mapped_column(Enum(LeadPriority))

    suggested_reply: Mapped[str] = mapped_column(Text)
    edited_reply: Mapped[str | None] = mapped_column(Text)
    status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus), default=LeadStatus.pending_review)
    published_url: Mapped[str | None] = mapped_column(Text)

    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
