# sox.bot Phase 3: CommunityBot 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 CommunityBot（社区管家），包含 Discord bot + RAG 技术问答知识库 + 企业线索识别 + 微信企业号机器人 + sox.bot 控制台社区管理界面。

**Architecture:** CommunityBot 共享核心 AI 引擎（意图识别 + RAG 回答），通过适配器接入不同平台（Discord/微信）。知识库基于 SoxAI 文档做 chunking → embedding → PGVector 存储，查询时做相似度搜索 + Claude 生成回答。

**Tech Stack:** discord.py, PGVector (pgvector extension), SoxAI Embedding API (text-embedding-3-small), 复用 Phase 1/2 的 FastAPI + Celery + PostgreSQL

---

## 文件结构

```
backend/
├── community/
│   ├── __init__.py
│   ├── rag.py                    # RAG 引擎（embedding + 检索 + 回答生成）
│   ├── intent.py                 # 意图识别（技术问题/新人/闲聊/企业信号/超出能力）
│   ├── responder.py              # 统一回答器（intent → 路由到不同处理逻辑）
│   ├── lead_detector.py          # 企业线索信号检测
│   ├── knowledge/
│   │   ├── __init__.py
│   │   ├── indexer.py            # 文档索引器（chunk + embed + upsert）
│   │   └── models.py             # KnowledgeChunk ORM 模型
│   └── platforms/
│       ├── __init__.py
│       ├── discord_bot.py        # Discord bot（discord.py）
│       └── wechat_bot.py         # 微信企业号 webhook handler
├── models/
│   ├── knowledge.py              # KnowledgeChunk + CommunityMessage ORM
│   └── ... (existing)
├── api/
│   ├── community.py              # /api/community 端点
│   └── ... (existing)
└── tests/
    ├── test_rag.py
    ├── test_intent.py
    ├── test_lead_detector.py
    └── ... (existing)

console/
└── src/app/community/
    └── page.tsx                  # 社区管理页面
```

---

### Task 1: Knowledge 数据模型 + PGVector 设置

**Files:**
- Create: `backend/models/knowledge.py`
- Create: `backend/schemas/community.py`
- Alembic migration (需要 pgvector extension)

```python
# models/knowledge.py
from datetime import datetime
from sqlalchemy import BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from models.lead import Base


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_file: Mapped[str] = mapped_column(String(500))  # e.g. "docs/api-reference/chat-completions.mdx"
    heading: Mapped[str] = mapped_column(String(500))       # section heading
    content: Mapped[str] = mapped_column(Text)              # chunk text
    embedding: Mapped[str] = mapped_column(Text)            # JSON array of floats (1536 dims)
    chunk_index: Mapped[int] = mapped_column(Integer)       # order within file
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CommunityMessage(Base):
    __tablename__ = "community_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    platform: Mapped[str] = mapped_column(String(50))       # discord, wechat
    channel_id: Mapped[str] = mapped_column(String(100))
    author_id: Mapped[str] = mapped_column(String(100))
    author_name: Mapped[str] = mapped_column(String(255))
    message_text: Mapped[str] = mapped_column(Text)
    intent: Mapped[str] = mapped_column(String(50))
    response_text: Mapped[str | None] = mapped_column(Text)
    escalated: Mapped[bool] = mapped_column(default=False)
    is_lead: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

Schemas:
```python
# schemas/community.py
from datetime import datetime
from pydantic import BaseModel


class MessageResponse(BaseModel):
    id: int
    platform: str
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
    model_config = {"from_attributes": True}


class CommunityStats(BaseModel):
    total_messages: int
    auto_resolved: int
    escalated: int
    leads_detected: int
    resolution_rate: float
```

- [ ] Generate Alembic migration
- [ ] Update models/__init__.py
- [ ] Commit

---

### Task 2: RAG 知识库引擎（文档索引 + 检索 + 回答）

**Files:**
- Create: `backend/community/__init__.py`
- Create: `backend/community/knowledge/__init__.py`
- Create: `backend/community/knowledge/indexer.py`
- Create: `backend/community/rag.py`
- Create: `backend/tests/test_rag.py`

Indexer:
```python
# community/knowledge/indexer.py
import json
import re
from dataclasses import dataclass
from openai import OpenAI
from config import settings


@dataclass
class Chunk:
    source_file: str
    heading: str
    content: str
    chunk_index: int


class KnowledgeIndexer:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.client = OpenAI(
            api_key=api_key or settings.soxai_api_key,
            base_url=base_url or settings.soxai_base_url,
        )

    def chunk_markdown(self, content: str, source_file: str) -> list[Chunk]:
        """Split markdown by ## headings into chunks."""
        sections = re.split(r'\n(?=## )', content)
        chunks = []
        for i, section in enumerate(sections):
            lines = section.strip().split('\n')
            heading = lines[0].lstrip('# ').strip() if lines else ""
            body = '\n'.join(lines[1:]).strip()
            if len(body) < 50:  # Skip tiny chunks
                continue
            chunks.append(Chunk(
                source_file=source_file,
                heading=heading,
                content=body,
                chunk_index=i,
            ))
        return chunks

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings via SoxAI API."""
        resp = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )
        return [d.embedding for d in resp.data]
```

RAG engine:
```python
# community/rag.py
import json
from dataclasses import dataclass
from openai import OpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from config import settings
from models.knowledge import KnowledgeChunk


@dataclass
class RAGResponse:
    answer: str
    sources: list[str]  # file paths of referenced chunks
    confidence: float   # 0-1


RAG_SYSTEM = """You are SoxBot, a helpful technical support assistant for SoxAI.
Answer the user's question based ONLY on the provided documentation context.
If the context doesn't contain enough information, say so honestly.
Always include a link to relevant docs when possible.
Keep answers concise (2-4 paragraphs max).
Tone: friendly, developer-to-developer."""


class RAGEngine:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.client = OpenAI(
            api_key=api_key or settings.soxai_api_key,
            base_url=base_url or settings.soxai_base_url,
        )

    def _embed_query(self, query: str) -> list[float]:
        resp = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=[query],
        )
        return resp.data[0].embedding

    async def search(self, query: str, db: AsyncSession, top_k: int = 5) -> list[KnowledgeChunk]:
        """Search knowledge base by cosine similarity."""
        query_embedding = self._embed_query(query)

        # Use Python-side similarity since we store embeddings as JSON text
        result = await db.execute(select(KnowledgeChunk))
        all_chunks = result.scalars().all()

        # Compute cosine similarity
        scored = []
        for chunk in all_chunks:
            chunk_emb = json.loads(chunk.embedding)
            sim = self._cosine_sim(query_embedding, chunk_emb)
            scored.append((sim, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]

    def generate_answer(self, question: str, context_chunks: list[KnowledgeChunk]) -> RAGResponse:
        context = "\n\n---\n\n".join([
            f"Source: {c.source_file}\n## {c.heading}\n{c.content}"
            for c in context_chunks
        ])

        resp = self.client.chat.completions.create(
            model="claude-sonnet-4-20250514",
            messages=[
                {"role": "system", "content": RAG_SYSTEM},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
            temperature=0.3,
        )

        sources = list(set(c.source_file for c in context_chunks))
        return RAGResponse(
            answer=resp.choices[0].message.content,
            sources=sources,
            confidence=0.8 if context_chunks else 0.2,
        )

    @staticmethod
    def _cosine_sim(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
```

Tests:
```python
# tests/test_rag.py
import pytest
from community.knowledge.indexer import KnowledgeIndexer, Chunk


class TestKnowledgeIndexer:
    def test_chunk_markdown_splits_by_heading(self):
        indexer = KnowledgeIndexer(api_key="test", base_url="https://api.soxai.io/v1")
        md = """## Getting Started
This is the getting started section with enough content to pass the minimum threshold.

## Authentication
API keys are required for all requests. You can create API keys in the console dashboard.

## Models
We support 200+ models from multiple providers including OpenAI, Anthropic, and Google.
"""
        chunks = indexer.chunk_markdown(md, "docs/quickstart.mdx")
        assert len(chunks) == 3
        assert chunks[0].heading == "Getting Started"
        assert chunks[1].heading == "Authentication"
        assert chunks[2].source_file == "docs/quickstart.mdx"

    def test_skips_tiny_chunks(self):
        indexer = KnowledgeIndexer(api_key="test", base_url="https://api.soxai.io/v1")
        md = """## Title
Short.

## Real Section
This section has enough content to be indexed properly and should not be skipped by the chunker.
"""
        chunks = indexer.chunk_markdown(md, "test.mdx")
        assert len(chunks) == 1
        assert chunks[0].heading == "Real Section"

    def test_chunk_has_required_fields(self):
        indexer = KnowledgeIndexer(api_key="test", base_url="https://api.soxai.io/v1")
        md = """## API Reference
The SoxAI API is OpenAI-compatible. Point your existing OpenAI SDK at our endpoint and it just works.
"""
        chunks = indexer.chunk_markdown(md, "docs/api.mdx")
        chunk = chunks[0]
        assert isinstance(chunk, Chunk)
        assert chunk.source_file == "docs/api.mdx"
        assert chunk.chunk_index == 0
```

- [ ] Run tests, verify pass
- [ ] Commit

---

### Task 3: 意图识别 + 企业线索检测

**Files:**
- Create: `backend/community/intent.py`
- Create: `backend/community/lead_detector.py`
- Create: `backend/tests/test_intent.py`
- Create: `backend/tests/test_lead_detector.py`

Intent classifier:
```python
# community/intent.py
import json
from openai import OpenAI
from config import settings


INTENT_SYSTEM = """Classify the user message intent. Return JSON with:
- "intent": one of "technical", "newbie", "chitchat", "enterprise", "beyond_scope"
  - technical: asking about API usage, errors, configuration, pricing
  - newbie: new user needing onboarding help, getting started
  - chitchat: casual conversation, feedback, compliments
  - enterprise: mentions team size, budget, compliance, private deployment, procurement
  - beyond_scope: questions not related to SoxAI or AI APIs at all
- "confidence": 0.0 to 1.0

Output JSON only."""


class IntentClassifier:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.client = OpenAI(
            api_key=api_key or settings.soxai_api_key,
            base_url=base_url or settings.soxai_base_url,
        )

    def classify(self, message: str) -> tuple[str, float]:
        resp = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": INTENT_SYSTEM},
                {"role": "user", "content": message},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        data = json.loads(resp.choices[0].message.content)
        return data["intent"], data.get("confidence", 0.5)
```

Lead detector (rule-based, no AI needed):
```python
# community/lead_detector.py
import re
from dataclasses import dataclass


@dataclass
class LeadSignal:
    detected: bool
    signal_type: str | None  # team_size, budget, compliance, migration, procurement
    confidence: str           # low, medium, high


SIGNAL_PATTERNS = {
    "team_size": [
        r'\b(\d{2,})\s*(developers?|engineers?|devs?|people|members?|人|开发者|工程师)',
        r'our team\s*(has|of|is)\s*\d+',
        r'我们团队有\s*\d+',
    ],
    "budget": [
        r'\$\d{3,}',
        r'budget\s*(of|is|around)\s*\$?\d+',
        r'预算.*\d+',
        r'每月.*\d+.*美元',
    ],
    "compliance": [
        r'private\s*deploy',
        r'self[- ]host',
        r'on[- ]premise',
        r'data\s*residen',
        r'complian',
        r'私有部署',
        r'数据.*出境',
        r'合规',
    ],
    "migration": [
        r'migrat(e|ing|ion)\s*(from|off)',
        r'switch(ing)?\s*(from|off)',
        r'从.*迁移',
        r'替换',
    ],
    "procurement": [
        r'quot(e|ation)',
        r'invoice',
        r'contract',
        r'purchase\s*order',
        r'报价',
        r'合同',
        r'采购',
    ],
}


class LeadDetector:
    def detect(self, message: str) -> LeadSignal:
        message_lower = message.lower()
        for signal_type, patterns in SIGNAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    confidence = "high" if signal_type in ("procurement", "budget") else "medium"
                    return LeadSignal(detected=True, signal_type=signal_type, confidence=confidence)
        return LeadSignal(detected=False, signal_type=None, confidence="low")
```

Tests:
```python
# tests/test_lead_detector.py
from community.lead_detector import LeadDetector


class TestLeadDetector:
    def setup_method(self):
        self.detector = LeadDetector()

    def test_detects_team_size(self):
        result = self.detector.detect("We have 50 developers using AI APIs")
        assert result.detected is True
        assert result.signal_type == "team_size"

    def test_detects_budget(self):
        result = self.detector.detect("Our monthly budget is $5000 for AI APIs")
        assert result.detected is True
        assert result.signal_type == "budget"
        assert result.confidence == "high"

    def test_detects_compliance_chinese(self):
        result = self.detector.detect("我们需要私有部署，数据不能出境")
        assert result.detected is True
        assert result.signal_type == "compliance"

    def test_detects_procurement(self):
        result = self.detector.detect("Can you provide a quotation for enterprise plan?")
        assert result.detected is True
        assert result.signal_type == "procurement"

    def test_no_signal_for_normal_message(self):
        result = self.detector.detect("How do I use the chat completions endpoint?")
        assert result.detected is False

    def test_detects_migration(self):
        result = self.detector.detect("We're migrating from OpenRouter to something more reliable")
        assert result.detected is True
        assert result.signal_type == "migration"
```

```python
# tests/test_intent.py — uses mock
import json
import pytest
from community.intent import IntentClassifier


@pytest.fixture
def mock_intent_api(httpx_mock):
    def _mock(intent="technical", confidence=0.9):
        httpx_mock.add_response(
            url="https://api.soxai.io/v1/chat/completions",
            json={
                "id": "mock",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": json.dumps({"intent": intent, "confidence": confidence})}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
            },
        )
    return _mock


class TestIntentClassifier:
    def test_classifies_technical(self, mock_intent_api):
        mock_intent_api(intent="technical")
        classifier = IntentClassifier(api_key="test", base_url="https://api.soxai.io/v1")
        intent, conf = classifier.classify("How do I set up failover routing?")
        assert intent == "technical"

    def test_classifies_enterprise(self, mock_intent_api):
        mock_intent_api(intent="enterprise", confidence=0.95)
        classifier = IntentClassifier(api_key="test", base_url="https://api.soxai.io/v1")
        intent, conf = classifier.classify("Our team of 200 needs private deployment")
        assert intent == "enterprise"
        assert conf >= 0.9
```

- [ ] Run tests, verify pass
- [ ] Commit

---

### Task 4: 统一回答器 + Discord bot

**Files:**
- Create: `backend/community/responder.py`
- Create: `backend/community/platforms/discord_bot.py`
- Create: `backend/community/platforms/__init__.py`

Responder (orchestrates intent → route → response):
```python
# community/responder.py
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from community.intent import IntentClassifier
from community.lead_detector import LeadDetector, LeadSignal
from community.rag import RAGEngine, RAGResponse


@dataclass
class BotResponse:
    text: str
    intent: str
    escalate: bool
    lead_signal: LeadSignal | None


WELCOME_MESSAGE = """Welcome to the SoxAI community! 🎉

Here's how to get started:
• **Quick Start**: https://docs.soxai.io/quickstart
• **Free $5 credit**: https://console.soxai.io/register
• **API Docs**: https://docs.soxai.io/api-reference

Ask me anything about SoxAI — I'm here to help!

If you're evaluating SoxAI for your enterprise team, let me know and I'll connect you with our team."""


class CommunityResponder:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.intent_classifier = IntentClassifier()
        self.lead_detector = LeadDetector()
        self.rag = RAGEngine()
        self._consecutive_failures: dict[str, int] = {}

    async def respond(self, message: str, author_id: str) -> BotResponse:
        # 1. Classify intent
        intent, confidence = self.intent_classifier.classify(message)

        # 2. Check for enterprise lead signals
        lead_signal = self.lead_detector.detect(message)

        # 3. Route based on intent
        if intent == "beyond_scope":
            return BotResponse(
                text="That's outside my area of expertise. I'm best at helping with SoxAI and AI API questions!",
                intent=intent, escalate=False, lead_signal=lead_signal,
            )

        if intent == "newbie":
            return BotResponse(
                text=WELCOME_MESSAGE, intent=intent, escalate=False, lead_signal=lead_signal,
            )

        if intent == "chitchat":
            return BotResponse(
                text="Thanks for the message! If you have any technical questions about SoxAI, I'm here to help.",
                intent=intent, escalate=False, lead_signal=lead_signal,
            )

        if intent in ("technical", "enterprise"):
            # RAG-powered answer
            chunks = await self.rag.search(message, self.db)
            if not chunks:
                return BotResponse(
                    text="I couldn't find relevant documentation for your question. Let me get a human colleague to help.",
                    intent=intent, escalate=True, lead_signal=lead_signal,
                )
            rag_response = self.rag.generate_answer(message, chunks)

            # Enterprise intent: add CTA
            suffix = ""
            if lead_signal and lead_signal.detected:
                suffix = "\n\n💼 It sounds like you might benefit from our enterprise features. I'll flag this for our team to follow up!"

            return BotResponse(
                text=rag_response.answer + suffix,
                intent=intent, escalate=lead_signal.detected if lead_signal else False,
                lead_signal=lead_signal,
            )

        # Fallback
        return BotResponse(
            text="Let me get a human colleague to help with this.",
            intent=intent, escalate=True, lead_signal=lead_signal,
        )
```

Discord bot:
```python
# community/platforms/discord_bot.py
import os
import discord
from discord.ext import commands

from database import async_session
from community.responder import CommunityResponder, WELCOME_MESSAGE
from models.knowledge import CommunityMessage


class SoxBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        print(f"SoxBot connected as {self.user}")

    async def on_member_join(self, member: discord.Member):
        # Send welcome DM
        try:
            await member.send(WELCOME_MESSAGE)
        except discord.Forbidden:
            pass  # DMs disabled

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not self.user.mentioned_in(message) and not isinstance(message.channel, discord.DMChannel):
            return  # Only respond to mentions or DMs

        async with async_session() as db:
            responder = CommunityResponder(db)
            clean_text = message.content.replace(f"<@{self.user.id}>", "").strip()
            result = await responder.respond(clean_text, str(message.author.id))

            # Log message
            msg_record = CommunityMessage(
                platform="discord",
                channel_id=str(message.channel.id),
                author_id=str(message.author.id),
                author_name=str(message.author),
                message_text=clean_text,
                intent=result.intent,
                response_text=result.text,
                escalated=result.escalate,
                is_lead=result.lead_signal.detected if result.lead_signal else False,
            )
            db.add(msg_record)
            await db.commit()

            await message.reply(result.text)


def run_discord_bot():
    token = os.environ.get("SOXBOT_DISCORD_TOKEN", "")
    if not token:
        print("SOXBOT_DISCORD_TOKEN not set, skipping Discord bot")
        return
    bot = SoxBot()
    bot.run(token)
```

- [ ] Commit

---

### Task 5: Community API + Celery 知识库同步

**Files:**
- Create: `backend/api/community.py`
- Modify: `backend/api/router.py`
- Modify: `backend/tasks/celery_app.py`
- Modify: `backend/config.py` (add discord token)

API endpoints:
```python
# api/community.py
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.knowledge import CommunityMessage, KnowledgeChunk
from schemas.community import MessageResponse, KnowledgeChunkResponse, CommunityStats

router = APIRouter(prefix="/api/community", tags=["community"])


@router.get("/messages", response_model=list[MessageResponse])
async def list_messages(
    escalated: bool | None = None,
    is_lead: bool | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(CommunityMessage).order_by(desc(CommunityMessage.created_at)).limit(limit)
    if escalated is not None:
        query = query.where(CommunityMessage.escalated == escalated)
    if is_lead is not None:
        query = query.where(CommunityMessage.is_lead == is_lead)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/stats", response_model=CommunityStats)
async def get_community_stats(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(CommunityMessage.id)))).scalar() or 0
    escalated = (await db.execute(
        select(func.count(CommunityMessage.id)).where(CommunityMessage.escalated == True)
    )).scalar() or 0
    leads = (await db.execute(
        select(func.count(CommunityMessage.id)).where(CommunityMessage.is_lead == True)
    )).scalar() or 0

    auto_resolved = total - escalated
    rate = (auto_resolved / total * 100) if total > 0 else 0.0

    return CommunityStats(
        total_messages=total,
        auto_resolved=auto_resolved,
        escalated=escalated,
        leads_detected=leads,
        resolution_rate=round(rate, 1),
    )


@router.get("/knowledge", response_model=list[KnowledgeChunkResponse])
async def list_knowledge(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(KnowledgeChunk).order_by(KnowledgeChunk.source_file, KnowledgeChunk.chunk_index).limit(limit)
    )
    return result.scalars().all()


@router.post("/knowledge/reindex", status_code=202)
async def trigger_reindex():
    from tasks.celery_app import reindex_knowledge_task
    reindex_knowledge_task.delay()
    return {"status": "queued", "message": "Knowledge base reindexing started"}
```

Celery task for knowledge reindexing:
```python
# Add to tasks/celery_app.py:

@celery.task
def reindex_knowledge_task():
    """Re-index SoxAI documentation into knowledge base."""
    import asyncio
    import glob
    import json
    from community.knowledge.indexer import KnowledgeIndexer
    from models.knowledge import KnowledgeChunk

    async def _reindex():
        indexer = KnowledgeIndexer()
        # Find all .mdx docs (would point to actual soxai website content)
        # For now, index any .md files in the sox-bot docs
        doc_files = glob.glob("docs/**/*.md", recursive=True)

        async with async_session() as db:
            # Clear existing chunks
            await db.execute(text("DELETE FROM knowledge_chunks"))

            for filepath in doc_files:
                with open(filepath) as f:
                    content = f.read()
                chunks = indexer.chunk_markdown(content, filepath)
                if not chunks:
                    continue

                # Batch embed
                texts = [c.content for c in chunks]
                embeddings = indexer.embed(texts)

                for chunk, embedding in zip(chunks, embeddings):
                    record = KnowledgeChunk(
                        source_file=chunk.source_file,
                        heading=chunk.heading,
                        content=chunk.content,
                        embedding=json.dumps(embedding),
                        chunk_index=chunk.chunk_index,
                    )
                    db.add(record)

            await db.commit()

    asyncio.run(_reindex())
    print("Knowledge base reindexed")
```

Config update — add to `backend/config.py`:
```python
    # Discord
    discord_token: str = ""
```

- [ ] Update router.py, celery_app.py, config.py
- [ ] Commit

---

### Task 6: sox.bot 控制台 — 社区管理页面

**Files:**
- Create: `console/src/app/community/page.tsx`
- Modify: `console/src/app/layout.tsx` (add nav)
- Modify: `console/src/lib/api.ts` (add community API)

Page features:
- Stats cards: total messages, auto-resolved, escalated, leads, resolution rate
- Two tabs: "Escalated" (messages needing human attention) / "Leads" (enterprise signals)
- Each message card: author, platform badge, intent badge, message text, bot response, lead signal type
- "Reindex Knowledge" button to trigger reindexing

- [ ] Build passes
- [ ] Commit + tag `sox-bot-v0.3.0`
