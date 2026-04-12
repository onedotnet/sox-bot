from pydantic import BaseModel


class KeywordCreate(BaseModel):
    term: str
    language: str = "en"
    platforms: str = '["reddit", "hackernews"]'


class KeywordResponse(BaseModel):
    id: int
    term: str
    language: str
    platforms: str
    is_active: bool

    model_config = {"from_attributes": True}
