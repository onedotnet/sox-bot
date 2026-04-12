# sox.bot Phase 2: ContentBot 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 ContentBot（内容工厂），实现多模型协作内容生成、内容日历自动排期、三层质量检查、多平台发布，以及 sox.bot 控制台的内容管理界面。

**Architecture:** ContentBot 复用 Phase 1 的 FastAPI + Celery 基础设施，新增 content 模块（生成管线 + 质量检查 + 发布适配器）。每周日自动生成下周内容计划，每篇内容经过 DeepSeek(大纲) → Claude(正文) → GPT-4o(翻译) → GPT-4o-mini(SEO) 四步多模型协作。

**Tech Stack:** 复用 Phase 1 全部技术栈 + SoxAI 多模型路由

---

## 文件结构

```
backend/
├── content/
│   ├── __init__.py
│   ├── generator.py              # 内容生成管线（多模型协作编排）
│   ├── quality.py                # 三层质量检查（事实核查 + 品牌一致性 + 平台适配）
│   ├── calendar.py               # 内容日历（自动排期 + CRUD）
│   ├── templates.py              # 内容类型模板（SEO长文/行业快评/教程/对比分析）
│   └── publishers/
│       ├── __init__.py
│       ├── base.py               # BaseContentPublisher 抽象基类
│       ├── twitter.py            # Twitter API v2 发布
│       └── blog.py               # soxai.io blog API（写入 MDX 文件）
├── models/
│   ├── content.py                # Content + ContentCalendar ORM 模型
│   └── ... (existing)
├── schemas/
│   ├── content.py                # Content Pydantic schemas
│   └── ... (existing)
├── api/
│   ├── content.py                # /api/content CRUD + 发布端点
│   ├── calendar.py               # /api/calendar 排期端点
│   └── ... (existing)
├── tasks/
│   └── celery_app.py             # 追加 content 定时任务
└── tests/
    ├── test_generator.py         # 内容生成管线测试
    ├── test_quality.py           # 质量检查测试
    ├── test_calendar.py          # 内容日历测试
    └── ... (existing)

console/
└── src/app/content/
    └── page.tsx                  # 内容管理页面（日历 + 草稿列表）
```

---

### Task 1: Content 数据模型 + Migration（SOX-204 前置）

**Files:**
- Create: `backend/models/content.py`
- Create: `backend/schemas/content.py`
- Create migration via Alembic

**Step 1: Content 模型**

```python
# models/content.py
import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from models.lead import Base


class ContentStatus(str, enum.Enum):
    draft = "draft"
    review = "review"
    approved = "approved"
    scheduled = "scheduled"
    published = "published"
    rejected = "rejected"


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


class Content(Base):
    __tablename__ = "contents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    content_type: Mapped[ContentType] = mapped_column(Enum(ContentType))
    language: Mapped[ContentLanguage] = mapped_column(Enum(ContentLanguage))
    status: Mapped[ContentStatus] = mapped_column(Enum(ContentStatus), default=ContentStatus.draft)

    # SEO
    seo_keyword: Mapped[str | None] = mapped_column(String(255))
    seo_tags: Mapped[str | None] = mapped_column(Text)  # JSON array

    # Multi-model tracking
    outline_model: Mapped[str | None] = mapped_column(String(100))  # e.g. "deepseek-chat"
    body_model: Mapped[str | None] = mapped_column(String(100))     # e.g. "claude-sonnet-4-20250514"
    translate_model: Mapped[str | None] = mapped_column(String(100)) # e.g. "gpt-4o"
    generation_cost_cents: Mapped[int] = mapped_column(Integer, default=0)  # cost in cents

    # Publishing
    target_platform: Mapped[str] = mapped_column(String(50))  # blog, twitter, zhihu, linkedin, v2ex
    published_url: Mapped[str | None] = mapped_column(Text)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Quality check
    quality_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    quality_notes: Mapped[str | None] = mapped_column(Text)

    # Pair tracking: original + translation share same pair_id
    pair_id: Mapped[str | None] = mapped_column(String(50))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())
```

- [ ] **Step 2: Pydantic schemas**

```python
# schemas/content.py
from datetime import datetime
from pydantic import BaseModel


class ContentResponse(BaseModel):
    id: int
    title: str
    body: str
    summary: str | None
    content_type: str
    language: str
    status: str
    seo_keyword: str | None
    target_platform: str
    published_url: str | None
    scheduled_at: datetime | None
    published_at: datetime | None
    quality_passed: bool
    quality_notes: str | None
    pair_id: str | None
    generation_cost_cents: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ContentUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    status: str | None = None
    scheduled_at: datetime | None = None


class ContentGenerateRequest(BaseModel):
    content_type: str = "seo_article"
    seo_keyword: str
    language: str = "en"
    target_platform: str = "blog"
    generate_translation: bool = True
```

- [ ] **Step 3: Generate Alembic migration + verify**

- [ ] **Step 4: Commit**

---

### Task 2: 多模型内容生成管线（SOX-204 核心）

**Files:**
- Create: `backend/content/__init__.py`
- Create: `backend/content/templates.py`
- Create: `backend/content/generator.py`
- Create: `backend/tests/test_generator.py`

**Step 1: 内容类型模板**

```python
# content/templates.py

OUTLINE_PROMPT = """You are a technical content strategist for SoxAI, an enterprise AI API gateway.

Generate a detailed outline for a {content_type} about "{keyword}".
Target audience: enterprise IT teams managing multiple AI API providers.

Requirements:
- 5-8 sections with clear headings
- Include practical code examples where relevant
- Include data points (pricing, performance comparisons)
- End with a clear CTA (not salesy — developer-to-developer tone)

Output format: JSON with "title" and "sections" (array of {{"heading": "...", "points": ["..."]}})
"""

BODY_PROMPT = """You are a senior technical writer producing content for SoxAI.

Write the full article based on this outline:
{outline}

Style guide:
- Developer-to-developer tone, not marketing
- Include code examples (Python/curl) where relevant
- Be honest about competitors — mention when they're better at something
- Include specific numbers (pricing, latency, etc.)
- {word_count_guide}
- Output in {language}

Format: Markdown with proper headings (## for sections).
"""

TRANSLATE_PROMPT = """Translate the following technical article from {source_lang} to {target_lang}.

Preserve:
- All code blocks unchanged
- Technical terms in their commonly used form in the target language
- Markdown formatting
- Links and URLs

Adapt:
- Idioms and cultural references
- Date/number formatting
- SEO keywords to target language equivalents

Article:
{body}
"""

SEO_PROMPT = """Optimize this article for SEO. Return JSON with:
- "title": SEO-optimized title (60 chars max)
- "summary": Meta description (155 chars max)
- "tags": Array of 5-8 relevant tags

Primary keyword: {keyword}
Language: {language}

Article title: {title}
First 500 chars: {preview}
"""

CONTENT_TYPE_CONFIG = {
    "seo_article": {"word_count": "1500-2000 words", "platforms": ["blog"]},
    "industry_brief": {"word_count": "300-500 words", "platforms": ["twitter", "zhihu"]},
    "tutorial": {"word_count": "1000-1500 words", "platforms": ["blog"]},
    "comparison": {"word_count": "2000-2500 words", "platforms": ["blog"]},
    "changelog": {"word_count": "200-400 words", "platforms": ["blog", "twitter", "discord"]},
    "social_post": {"word_count": "50-280 characters", "platforms": ["twitter"]},
}
```

**Step 2: 内容生成器**

```python
# content/generator.py
import json
import uuid
from dataclasses import dataclass

from openai import OpenAI

from config import settings
from content.templates import (
    OUTLINE_PROMPT, BODY_PROMPT, TRANSLATE_PROMPT, SEO_PROMPT, CONTENT_TYPE_CONFIG
)


@dataclass
class GeneratedContent:
    title: str
    body: str
    summary: str
    seo_tags: list[str]
    outline_model: str
    body_model: str
    cost_estimate_cents: int


class ContentGenerator:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.client = OpenAI(
            api_key=api_key or settings.soxai_api_key,
            base_url=base_url or settings.soxai_base_url,
        )

    def _call(self, model: str, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.7,
        )
        return resp.choices[0].message.content

    def _call_json(self, model: str, system: str, user: str) -> dict:
        resp = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)

    def generate(self, keyword: str, content_type: str = "seo_article",
                 language: str = "en") -> GeneratedContent:
        config = CONTENT_TYPE_CONFIG.get(content_type, CONTENT_TYPE_CONFIG["seo_article"])

        # Step 1: Outline (DeepSeek — cheap, good at structure)
        outline_data = self._call_json(
            model="deepseek-chat",
            system="You are a content strategist. Output valid JSON only.",
            user=OUTLINE_PROMPT.format(content_type=content_type, keyword=keyword),
        )

        # Step 2: Body (Claude Sonnet — best writing quality)
        lang_name = "English" if language == "en" else "Chinese (Simplified)"
        body = self._call(
            model="claude-sonnet-4-20250514",
            system="You are a senior technical writer.",
            user=BODY_PROMPT.format(
                outline=json.dumps(outline_data, ensure_ascii=False),
                word_count_guide=config["word_count"],
                language=lang_name,
            ),
        )

        # Step 3: SEO optimization (GPT-4o-mini — cheap, good enough)
        seo = self._call_json(
            model="gpt-4o-mini",
            system="You are an SEO specialist. Output valid JSON only.",
            user=SEO_PROMPT.format(
                keyword=keyword,
                language=language,
                title=outline_data.get("title", keyword),
                preview=body[:500],
            ),
        )

        return GeneratedContent(
            title=seo.get("title", outline_data.get("title", keyword)),
            body=body,
            summary=seo.get("summary", ""),
            seo_tags=seo.get("tags", []),
            outline_model="deepseek-chat",
            body_model="claude-sonnet-4-20250514",
            cost_estimate_cents=9,  # ~$0.09 per article
        )

    def translate(self, body: str, source_lang: str = "en",
                  target_lang: str = "zh") -> str:
        src = "English" if source_lang == "en" else "Chinese"
        tgt = "Chinese (Simplified)" if target_lang == "zh" else "English"
        return self._call(
            model="gpt-4o",
            system="You are a professional translator specializing in technical content.",
            user=TRANSLATE_PROMPT.format(
                source_lang=src, target_lang=tgt, body=body
            ),
        )
```

**Step 3: 测试**

```python
# tests/test_generator.py
import json
import pytest

from content.generator import ContentGenerator, GeneratedContent


@pytest.fixture
def mock_content_api(httpx_mock):
    """Mock multi-model calls for content generation"""
    # All calls go to the same endpoint, return appropriate content
    def add_mock(content_text, is_json=False):
        body = content_text if not is_json else json.dumps(content_text)
        httpx_mock.add_response(
            url="https://api.soxai.io/v1/chat/completions",
            json={
                "id": "mock",
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": body},
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
            },
        )

    # 1st call: outline (JSON)
    add_mock({"title": "AI API Gateway Guide", "sections": [
        {"heading": "Introduction", "points": ["Why multi-model matters"]},
        {"heading": "Architecture", "points": ["Gateway pattern"]},
    ]}, is_json=True)

    # 2nd call: body (text)
    add_mock("## Introduction\n\nThis is a comprehensive guide to AI API gateways...")

    # 3rd call: SEO (JSON)
    add_mock({"title": "AI API Gateway: Complete Guide 2026", "summary": "Learn how to manage multiple AI providers with a unified gateway.", "tags": ["AI", "API", "gateway"]}, is_json=True)


class TestContentGenerator:
    def test_generate_returns_content(self, mock_content_api):
        gen = ContentGenerator(api_key="test", base_url="https://api.soxai.io/v1")
        result = gen.generate(keyword="AI API gateway", content_type="seo_article")
        assert isinstance(result, GeneratedContent)
        assert len(result.title) > 0
        assert len(result.body) > 0
        assert len(result.summary) > 0
        assert result.outline_model == "deepseek-chat"
        assert result.body_model == "claude-sonnet-4-20250514"

    def test_generate_has_seo_tags(self, mock_content_api):
        gen = ContentGenerator(api_key="test", base_url="https://api.soxai.io/v1")
        result = gen.generate(keyword="AI API gateway")
        assert isinstance(result.seo_tags, list)
        assert len(result.seo_tags) > 0
```

- [ ] **Step 4: Run tests, verify pass**
- [ ] **Step 5: Commit**

---

### Task 3: 质量检查管线（SOX-204 中）

**Files:**
- Create: `backend/content/quality.py`
- Create: `backend/tests/test_quality.py`

**Step 1: 质量检查器**

```python
# content/quality.py
import json
import re
from dataclasses import dataclass


@dataclass
class QualityResult:
    passed: bool
    notes: str
    checks: dict[str, bool]


class QualityChecker:
    # Brand terms that must be spelled correctly
    BRAND_TERMS = {
        "SoxAI": ["soxai", "SoxAi", "SOXAI", "Sox AI", "sox.ai"],
        "OpenRouter": ["openrouter", "Open Router", "Openrouter"],
    }

    # Platform constraints
    PLATFORM_LIMITS = {
        "twitter": {"max_chars": 280},
        "zhihu": {"min_chars": 500},
        "blog": {"min_chars": 1000},
        "linkedin": {"max_chars": 3000},
    }

    def check(self, title: str, body: str, platform: str, language: str) -> QualityResult:
        checks = {}

        # 1. Fact check: no obviously wrong claims
        checks["no_false_claims"] = self._check_facts(body)

        # 2. Brand consistency
        checks["brand_consistent"] = self._check_brand(body)

        # 3. Platform adaptation
        checks["platform_adapted"] = self._check_platform(body, platform)

        # 4. No placeholder content
        checks["no_placeholders"] = self._check_placeholders(body)

        # 5. Has proper formatting
        checks["proper_format"] = self._check_format(body, platform)

        passed = all(checks.values())
        failed = [k for k, v in checks.items() if not v]
        notes = "All checks passed." if passed else f"Failed: {', '.join(failed)}"

        return QualityResult(passed=passed, notes=notes, checks=checks)

    def _check_facts(self, body: str) -> bool:
        # Flag obvious issues: wrong URLs, outdated claims
        wrong_urls = ["api.soxai.com", "www.soxai.com/api"]
        return not any(url in body for url in wrong_urls)

    def _check_brand(self, body: str) -> bool:
        for correct, wrong_list in self.BRAND_TERMS.items():
            for wrong in wrong_list:
                if wrong in body and correct not in body:
                    return False
        return True

    def _check_platform(self, body: str, platform: str) -> bool:
        limits = self.PLATFORM_LIMITS.get(platform)
        if not limits:
            return True
        if "max_chars" in limits and len(body) > limits["max_chars"]:
            return False
        if "min_chars" in limits and len(body) < limits["min_chars"]:
            return False
        return True

    def _check_placeholders(self, body: str) -> bool:
        placeholders = ["[TODO]", "[INSERT", "[PLACEHOLDER", "Lorem ipsum", "TBD"]
        return not any(p.lower() in body.lower() for p in placeholders)

    def _check_format(self, body: str, platform: str) -> bool:
        if platform == "blog":
            return "##" in body  # Should have markdown headings
        return True
```

**Step 2: 测试**

```python
# tests/test_quality.py
from content.quality import QualityChecker


class TestQualityChecker:
    def setup_method(self):
        self.checker = QualityChecker()

    def test_passes_good_blog_content(self):
        result = self.checker.check(
            title="AI API Gateway Guide",
            body="## Introduction\n\nSoxAI provides a unified gateway for AI APIs. " * 50,
            platform="blog",
            language="en",
        )
        assert result.passed is True

    def test_fails_wrong_brand_spelling(self):
        result = self.checker.check(
            title="Test",
            body="## Intro\n\nsoxai is great. " * 50,
            platform="blog",
            language="en",
        )
        assert result.checks["brand_consistent"] is False

    def test_fails_twitter_too_long(self):
        result = self.checker.check(
            title="Test",
            body="A" * 300,
            platform="twitter",
            language="en",
        )
        assert result.checks["platform_adapted"] is False

    def test_fails_placeholder_content(self):
        result = self.checker.check(
            title="Test",
            body="## Intro\n\n[TODO] add content here. " * 50,
            platform="blog",
            language="en",
        )
        assert result.checks["no_placeholders"] is False

    def test_fails_blog_without_headings(self):
        result = self.checker.check(
            title="Test",
            body="Just plain text without any markdown headings. " * 100,
            platform="blog",
            language="en",
        )
        assert result.checks["proper_format"] is False
```

- [ ] **Step 3: Run tests, verify pass**
- [ ] **Step 4: Commit**

---

### Task 4: 内容日历 + 自动排期（SOX-204 后半）

**Files:**
- Create: `backend/content/calendar.py`
- Create: `backend/tests/test_calendar.py`

**Step 1: 日历管理器**

```python
# content/calendar.py
from datetime import datetime, timedelta, timezone

from content.templates import CONTENT_TYPE_CONFIG

# Weekly schedule template
WEEKLY_SCHEDULE = [
    {"weekday": 0, "content_type": "seo_article", "language": "en", "platform": "blog"},      # Monday
    {"weekday": 1, "content_type": "industry_brief", "language": "en", "platform": "twitter"},  # Tuesday
    {"weekday": 2, "content_type": "seo_article", "language": "zh", "platform": "blog"},        # Wednesday
    {"weekday": 3, "content_type": "social_post", "language": "en", "platform": "twitter"},     # Thursday
    {"weekday": 4, "content_type": "industry_brief", "language": "en", "platform": "linkedin"}, # Friday
]


class ContentCalendar:
    def generate_weekly_plan(self, start_date: datetime,
                             keywords: list[str]) -> list[dict]:
        """Generate a weekly content plan starting from start_date."""
        plan = []
        kw_index = 0

        for slot in WEEKLY_SCHEDULE:
            target_date = start_date + timedelta(days=slot["weekday"])
            keyword = keywords[kw_index % len(keywords)] if keywords else "AI API gateway"
            kw_index += 1

            plan.append({
                "scheduled_at": target_date.replace(hour=9, minute=0, tzinfo=timezone.utc),
                "content_type": slot["content_type"],
                "language": slot["language"],
                "target_platform": slot["platform"],
                "seo_keyword": keyword,
            })

        return plan

    def get_next_monday(self, from_date: datetime | None = None) -> datetime:
        """Get the next Monday from a given date."""
        d = from_date or datetime.now(timezone.utc)
        days_ahead = 7 - d.weekday()  # Monday is 0
        if days_ahead == 7:
            days_ahead = 0
        return (d + timedelta(days=days_ahead)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
```

**Step 2: 测试**

```python
# tests/test_calendar.py
from datetime import datetime, timezone
from content.calendar import ContentCalendar


class TestContentCalendar:
    def setup_method(self):
        self.cal = ContentCalendar()

    def test_generates_5_slots(self):
        monday = datetime(2026, 4, 13, tzinfo=timezone.utc)
        plan = self.cal.generate_weekly_plan(monday, keywords=["AI API", "LLM proxy"])
        assert len(plan) == 5

    def test_slots_have_required_fields(self):
        monday = datetime(2026, 4, 13, tzinfo=timezone.utc)
        plan = self.cal.generate_weekly_plan(monday, keywords=["AI API"])
        for slot in plan:
            assert "scheduled_at" in slot
            assert "content_type" in slot
            assert "language" in slot
            assert "target_platform" in slot
            assert "seo_keyword" in slot

    def test_rotates_keywords(self):
        monday = datetime(2026, 4, 13, tzinfo=timezone.utc)
        plan = self.cal.generate_weekly_plan(monday, keywords=["kw1", "kw2"])
        keywords_used = [s["seo_keyword"] for s in plan]
        assert "kw1" in keywords_used
        assert "kw2" in keywords_used

    def test_get_next_monday(self):
        # Wednesday April 15
        wed = datetime(2026, 4, 15, 14, 30, tzinfo=timezone.utc)
        monday = self.cal.get_next_monday(wed)
        assert monday.weekday() == 0  # Monday
        assert monday.day == 20  # Next Monday is April 20
```

- [ ] **Step 3: Run tests, verify pass**
- [ ] **Step 4: Commit**

---

### Task 5: Content API 端点 + Celery 任务（SOX-205 前半）

**Files:**
- Create: `backend/api/content.py`
- Create: `backend/api/calendar_api.py`
- Modify: `backend/api/router.py` (register new routes)
- Modify: `backend/tasks/celery_app.py` (add content tasks)
- Modify: `backend/models/__init__.py` (export new models)

**Step 1: Content API**

```python
# api/content.py
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.content import Content, ContentStatus
from schemas.content import ContentResponse, ContentUpdate, ContentGenerateRequest

router = APIRouter(prefix="/api/content", tags=["content"])


@router.get("", response_model=list[ContentResponse])
async def list_content(
    status: str | None = None,
    content_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(Content).order_by(desc(Content.created_at)).limit(limit).offset(offset)
    if status:
        query = query.where(Content.status == status)
    if content_type:
        query = query.where(Content.content_type == content_type)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    return content


@router.patch("/{content_id}", response_model=ContentResponse)
async def update_content(content_id: int, body: ContentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    if body.title is not None:
        content.title = body.title
    if body.body is not None:
        content.body = body.body
    if body.status is not None:
        content.status = ContentStatus(body.status)
    if body.scheduled_at is not None:
        content.scheduled_at = body.scheduled_at
    content.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(content)
    return content


@router.post("/generate", status_code=202)
async def generate_content(req: ContentGenerateRequest):
    """Trigger async content generation via Celery"""
    from tasks.celery_app import generate_content_task
    generate_content_task.delay(
        keyword=req.seo_keyword,
        content_type=req.content_type,
        language=req.language,
        target_platform=req.target_platform,
        generate_translation=req.generate_translation,
    )
    return {"status": "queued", "message": "Content generation started"}
```

**Step 2: Calendar API**

```python
# api/calendar_api.py
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.content import Content
from schemas.content import ContentResponse

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("", response_model=list[ContentResponse])
async def get_calendar(
    week_start: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get scheduled content for a given week."""
    query = select(Content).where(
        Content.scheduled_at.isnot(None)
    ).order_by(Content.scheduled_at)
    if week_start:
        start = datetime.fromisoformat(week_start)
        from datetime import timedelta
        end = start + timedelta(days=7)
        query = query.where(
            and_(Content.scheduled_at >= start, Content.scheduled_at < end)
        )
    result = await db.execute(query)
    return result.scalars().all()
```

**Step 3: Update router.py**

```python
# Add to api/router.py:
from api.content import router as content_router
from api.calendar_api import router as calendar_router

api_router.include_router(content_router)
api_router.include_router(calendar_router)
```

**Step 4: Update celery_app.py**

```python
# Add to tasks/celery_app.py:

@celery.task
def generate_content_task(keyword: str, content_type: str = "seo_article",
                          language: str = "en", target_platform: str = "blog",
                          generate_translation: bool = True):
    """Generate content asynchronously"""
    import asyncio
    import uuid
    from content.generator import ContentGenerator
    from content.quality import QualityChecker
    from database import async_session
    from models.content import Content, ContentStatus, ContentType, ContentLanguage

    async def _generate():
        gen = ContentGenerator()
        checker = QualityChecker()

        # Generate content
        result = gen.generate(keyword=keyword, content_type=content_type, language=language)

        # Quality check
        qc = checker.check(result.title, result.body, target_platform, language)

        pair_id = str(uuid.uuid4())[:8]

        async with async_session() as db:
            content = Content(
                title=result.title,
                body=result.body,
                summary=result.summary,
                content_type=ContentType(content_type),
                language=ContentLanguage(language),
                status=ContentStatus.review if qc.passed else ContentStatus.draft,
                seo_keyword=keyword,
                seo_tags=str(result.seo_tags),
                outline_model=result.outline_model,
                body_model=result.body_model,
                generation_cost_cents=result.cost_estimate_cents,
                target_platform=target_platform,
                quality_passed=qc.passed,
                quality_notes=qc.notes,
                pair_id=pair_id,
            )
            db.add(content)

            # Generate translation if requested
            if generate_translation:
                target_lang = "zh" if language == "en" else "en"
                translated_body = gen.translate(result.body, language, target_lang)
                trans_qc = checker.check(result.title, translated_body,
                                         target_platform, target_lang)
                translation = Content(
                    title=f"[{target_lang.upper()}] {result.title}",
                    body=translated_body,
                    summary=result.summary,
                    content_type=ContentType(content_type),
                    language=ContentLanguage(target_lang),
                    status=ContentStatus.review if trans_qc.passed else ContentStatus.draft,
                    seo_keyword=keyword,
                    outline_model=result.outline_model,
                    body_model=result.body_model,
                    translate_model="gpt-4o",
                    generation_cost_cents=3,  # translation cost
                    target_platform=target_platform,
                    quality_passed=trans_qc.passed,
                    quality_notes=trans_qc.notes,
                    pair_id=pair_id,
                )
                db.add(translation)

            await db.commit()

    asyncio.run(_generate())
    print(f"Content generated for keyword: {keyword}")


# Add weekly plan generation to beat schedule
celery.conf.beat_schedule["generate-weekly-plan"] = {
    "task": "tasks.celery_app.generate_weekly_plan_task",
    "schedule": crontab(day_of_week="sunday", hour=20, minute=0),  # Sunday 8pm UTC
}


@celery.task
def generate_weekly_plan_task():
    """Generate next week's content plan every Sunday"""
    import asyncio
    from content.calendar import ContentCalendar
    from database import async_session
    from models.keyword import Keyword
    from sqlalchemy import select

    async def _plan():
        cal = ContentCalendar()
        monday = cal.get_next_monday()

        async with async_session() as db:
            result = await db.execute(
                select(Keyword).where(Keyword.is_active == True)
            )
            keywords = [k.term for k in result.scalars().all()]

        plan = cal.generate_weekly_plan(monday, keywords)

        # Queue content generation for each slot
        for slot in plan:
            generate_content_task.delay(
                keyword=slot["seo_keyword"],
                content_type=slot["content_type"],
                language=slot["language"],
                target_platform=slot["target_platform"],
            )

        print(f"Weekly plan generated: {len(plan)} content pieces queued")

    asyncio.run(_plan())
```

- [ ] **Step 5: Update models/__init__.py to export Content**
- [ ] **Step 6: Run all tests, verify pass**
- [ ] **Step 7: Commit**

---

### Task 6: sox.bot 控制台 — 内容管理页面（SOX-205 后半）

**Files:**
- Create: `console/src/app/content/page.tsx`
- Modify: `console/src/app/layout.tsx` (add nav item)
- Modify: `console/src/lib/api.ts` (add content API functions)

**Step 1: Add content API functions to api.ts**

```typescript
// Add to src/lib/api.ts:

export interface ContentItem {
  id: number;
  title: string;
  body: string;
  summary: string | null;
  content_type: string;
  language: string;
  status: string;
  seo_keyword: string | null;
  target_platform: string;
  published_url: string | null;
  scheduled_at: string | null;
  quality_passed: boolean;
  quality_notes: string | null;
  pair_id: string | null;
  generation_cost_cents: number;
  created_at: string;
}

export async function fetchContent(params?: { status?: string; content_type?: string }): Promise<ContentItem[]> {
  const url = new URL(`${API_BASE}/api/content`);
  if (params?.status) url.searchParams.set("status", params.status);
  if (params?.content_type) url.searchParams.set("content_type", params.content_type);
  const res = await fetch(url.toString());
  return res.json();
}

export async function updateContent(id: number, data: { title?: string; body?: string; status?: string }) {
  const res = await fetch(`${API_BASE}/api/content/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function generateContent(data: { seo_keyword: string; content_type?: string; language?: string }) {
  const res = await fetch(`${API_BASE}/api/content/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function fetchCalendar(weekStart?: string): Promise<ContentItem[]> {
  const url = new URL(`${API_BASE}/api/calendar`);
  if (weekStart) url.searchParams.set("week_start", weekStart);
  const res = await fetch(url.toString());
  return res.json();
}
```

**Step 2: Content management page**

Create a page with:
- Tab view: "Drafts" / "Scheduled" / "Published"
- Each content card shows: title, type badge, language badge, platform, quality status
- Actions: Approve → Schedule, Edit, Reject, Generate New
- "Generate" button that triggers content generation with keyword input

**Step 3: Add "Content" nav item to layout.tsx sidebar**

**Step 4: Verify `bun run build` passes**

**Step 5: Commit**
