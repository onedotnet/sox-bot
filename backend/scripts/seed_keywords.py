"""Insert initial monitoring keywords"""
import asyncio
import sys
import os

# Add backend to path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, async_session
from models.lead import Base
from models.keyword import Keyword

SEED_KEYWORDS = [
    # English
    {"term": "AI API gateway", "language": "en", "platforms": '["reddit", "hackernews"]'},
    {"term": "openrouter alternative", "language": "en", "platforms": '["reddit", "hackernews", "twitter"]'},
    {"term": "LLM proxy", "language": "en", "platforms": '["reddit", "hackernews"]'},
    {"term": "manage AI API keys", "language": "en", "platforms": '["reddit"]'},
    {"term": "AI cost management", "language": "en", "platforms": '["reddit", "hackernews", "twitter"]'},
    {"term": "multi-provider failover", "language": "en", "platforms": '["reddit", "hackernews"]'},
    {"term": "AI API pricing", "language": "en", "platforms": '["hackernews", "twitter"]'},
    # Chinese
    {"term": "大模型网关", "language": "zh", "platforms": '["zhihu", "v2ex"]'},
    {"term": "AI API 管理", "language": "zh", "platforms": '["zhihu", "v2ex"]'},
    {"term": "多模型调用", "language": "zh", "platforms": '["zhihu", "v2ex"]'},
    {"term": "OpenRouter 替代", "language": "zh", "platforms": '["zhihu", "v2ex"]'},
    {"term": "API 中转", "language": "zh", "platforms": '["zhihu", "v2ex"]'},
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as db:
        for kw_data in SEED_KEYWORDS:
            kw = Keyword(**kw_data)
            db.add(kw)
        await db.commit()
        print(f"Seeded {len(SEED_KEYWORDS)} keywords")


if __name__ == "__main__":
    asyncio.run(seed())
