from datetime import datetime

from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: int
    platform: str
    channel_id: str
    author_id: str
    author_name: str
    message_text: str
    intent: str
    response_text: str | None
    escalated: bool
    is_lead: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeChunkResponse(BaseModel):
    id: int
    source_file: str
    heading: str
    content: str
    chunk_index: int
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class CommunityStats(BaseModel):
    total_messages: int
    auto_resolved: int
    escalated: int
    leads_detected: int
    resolution_rate: float
