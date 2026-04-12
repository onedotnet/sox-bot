from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from models.lead import Base


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    week_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    week_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # ScoutBot metrics
    leads_discovered: Mapped[int] = mapped_column(Integer, default=0)
    leads_published: Mapped[int] = mapped_column(Integer, default=0)
    enterprise_leads: Mapped[int] = mapped_column(Integer, default=0)

    # ContentBot metrics
    content_generated: Mapped[int] = mapped_column(Integer, default=0)
    content_published: Mapped[int] = mapped_column(Integer, default=0)
    content_cost_cents: Mapped[int] = mapped_column(Integer, default=0)

    # CommunityBot metrics
    messages_received: Mapped[int] = mapped_column(Integer, default=0)
    messages_auto_resolved: Mapped[int] = mapped_column(Integer, default=0)
    messages_escalated: Mapped[int] = mapped_column(Integer, default=0)
    community_leads: Mapped[int] = mapped_column(Integer, default=0)
    resolution_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # AI-generated insights
    summary: Mapped[str] = mapped_column(Text)
    action_items: Mapped[str] = mapped_column(Text)  # JSON array of suggestions

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
