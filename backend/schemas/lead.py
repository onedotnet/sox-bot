from datetime import datetime
from pydantic import BaseModel


class LeadResponse(BaseModel):
    id: int
    source: str
    source_url: str
    author: str
    original_text: str
    subreddit: str | None
    relevance_score: int
    intent: str
    sentiment: str
    priority: str
    suggested_reply: str
    edited_reply: str | None
    status: str
    published_url: str | None
    detected_at: datetime
    reviewed_at: datetime | None
    published_at: datetime | None

    model_config = {"from_attributes": True}


class LeadUpdate(BaseModel):
    status: str | None = None
    edited_reply: str | None = None
