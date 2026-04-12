# sox.bot Phase 1: 基础设施 + ScoutBot 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建 sox.bot Python 后端，实现 ScoutBot（线索猎手）完整功能，部署 sox.bot 控制台供审核使用。

**Architecture:** FastAPI 后端 + Celery 定时任务 + PostgreSQL 存储 + SoxAI API 作为 AI 引擎。ScoutBot 每 30 分钟扫描多平台关键词讨论，AI 分析后生成线索卡片，通过 Next.js 控制台审核发布。

**Tech Stack:** Python 3.12, FastAPI, Celery, Redis, PostgreSQL, OpenAI SDK (pointed at SoxAI), Next.js 15, shadcn/ui, Tailwind CSS

---

## 文件结构

```
sox-bot/                              # 独立 repo: github.com/onedotnet/sox-bot
├── backend/
│   ├── main.py                       # FastAPI 入口
│   ├── config.py                     # 环境变量配置（pydantic-settings）
│   ├── database.py                   # SQLAlchemy async engine + session
│   ├── models/
│   │   ├── __init__.py
│   │   ├── lead.py                   # Lead ORM 模型（线索卡片）
│   │   └── keyword.py                # Keyword ORM 模型（监控关键词）
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── lead.py                   # Lead Pydantic schema
│   │   └── keyword.py                # Keyword Pydantic schema
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py                 # API 路由注册
│   │   ├── leads.py                  # /api/leads CRUD 端点
│   │   ├── keywords.py               # /api/keywords CRUD 端点
│   │   └── dashboard.py              # /api/dashboard 统计端点
│   ├── scout/
│   │   ├── __init__.py
│   │   ├── engine.py                 # ScoutBot 主引擎（编排采集→分析→存储）
│   │   ├── analyzer.py               # AI 分析层（SoxAI API 调用）
│   │   ├── dedup.py                  # 去重 + 过滤逻辑
│   │   └── platforms/
│   │       ├── __init__.py
│   │       ├── base.py               # BasePlatform 抽象基类
│   │       ├── reddit.py             # Reddit API 采集器
│   │       ├── hackernews.py         # HN Algolia API 采集器
│   │       └── twitter.py            # Twitter API v2 采集器
│   ├── publisher/
│   │   ├── __init__.py
│   │   ├── manager.py                # 发布管理器（审核后触发）
│   │   └── platforms/
│   │       ├── __init__.py
│   │       ├── base.py               # BasePublisher 抽象基类
│   │       └── reddit.py             # Reddit 回复发布
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── celery_app.py             # Celery 实例 + 定时任务定义
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py               # pytest fixtures（test DB, mock SoxAI）
│   │   ├── test_analyzer.py          # AI 分析层测试
│   │   ├── test_dedup.py             # 去重逻辑测试
│   │   ├── test_reddit_collector.py  # Reddit 采集器测试
│   │   ├── test_hn_collector.py      # HN 采集器测试
│   │   ├── test_leads_api.py         # Leads API 端点测试
│   │   └── test_publisher.py         # 发布管道测试
│   ├── alembic/                      # DB migration
│   │   ├── env.py
│   │   └── versions/
│   ├── alembic.ini
│   ├── pyproject.toml                # 项目依赖（uv/pip）
│   ├── Dockerfile
│   └── docker-compose.yml            # dev 环境（PG + Redis + API + Celery worker）
└── console/                          # sox.bot Next.js 控制台（Phase 1 精简版）
    ├── package.json
    ├── src/
    │   ├── app/
    │   │   ├── layout.tsx
    │   │   ├── page.tsx              # → redirect /dashboard
    │   │   ├── dashboard/
    │   │   │   └── page.tsx          # 总览仪表盘
    │   │   └── scout/
    │   │       └── page.tsx          # ScoutBot 线索审核
    │   ├── components/
    │   │   ├── lead-card.tsx          # 线索卡片组件
    │   │   ├── keyword-manager.tsx    # 关键词配置组件
    │   │   └── stats-card.tsx         # 统计卡片组件
    │   └── lib/
    │       └── api.ts                 # API 客户端
    └── Dockerfile
```

---

### Task 1: 项目骨架 + 配置 + 数据库（SOX-200 前半）

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/config.py`
- Create: `backend/database.py`
- Create: `backend/main.py`
- Create: `backend/docker-compose.yml`

- [ ] **Step 1: 创建 pyproject.toml**

```toml
[project]
name = "sox-bot"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.34.0",
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "pydantic-settings>=2.7.0",
    "celery[redis]>=5.4.0",
    "openai>=1.60.0",
    "httpx>=0.28.0",
    "praw>=7.8.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-httpx>=0.35.0",
    "httpx>=0.28.0",
]
```

- [ ] **Step 2: 创建 config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://soxbot:soxbot@localhost:5432/soxbot"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # SoxAI API
    soxai_api_key: str = ""
    soxai_base_url: str = "https://api.soxai.io/v1"

    # ScoutBot
    scout_interval_minutes: int = 30
    scout_relevance_threshold: int = 60
    scout_max_replies_per_platform_per_day: int = 5
    scout_cooldown_days: int = 30

    # Reddit
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_username: str = ""
    reddit_password: str = ""

    # Twitter
    twitter_bearer_token: str = ""

    model_config = {"env_prefix": "SOXBOT_"}


settings = Settings()
```

- [ ] **Step 3: 创建 database.py**

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
```

- [ ] **Step 4: 创建 main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="sox.bot", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sox.bot", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
```

- [ ] **Step 5: 创建 docker-compose.yml**

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: soxbot
      POSTGRES_USER: soxbot
      POSTGRES_PASSWORD: soxbot
    ports:
      - "5433:5432"
    volumes:
      - soxbot_pg_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"

  api:
    build: .
    ports:
      - "8090:8090"
    environment:
      SOXBOT_DATABASE_URL: postgresql+asyncpg://soxbot:soxbot@postgres:5432/soxbot
      SOXBOT_REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  worker:
    build: .
    command: celery -A tasks.celery_app worker -l info -B
    environment:
      SOXBOT_DATABASE_URL: postgresql+asyncpg://soxbot:soxbot@postgres:5432/soxbot
      SOXBOT_REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis

volumes:
  soxbot_pg_data:
```

- [ ] **Step 6: 验证启动**

Run: `cd backend && pip install -e ".[dev]" && uvicorn main:app --port 8090`
Expected: Server starts, `curl localhost:8090/healthz` returns `{"status":"ok"}`

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat(sox-bot): project skeleton — FastAPI + config + database + docker-compose (SOX-200)"
```

---

### Task 2: 数据库模型 + Migration（SOX-200 后半）

**Files:**
- Create: `backend/models/__init__.py`
- Create: `backend/models/lead.py`
- Create: `backend/models/keyword.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`

- [ ] **Step 1: 创建 Lead 模型**

```python
# models/lead.py
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
    source: Mapped[str] = mapped_column(String(50))  # reddit, hackernews, twitter, zhihu, v2ex
    source_id: Mapped[str] = mapped_column(String(255), unique=True)  # 平台原始 ID，用于去重
    source_url: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(String(255))
    original_text: Mapped[str] = mapped_column(Text)
    subreddit: Mapped[str | None] = mapped_column(String(100))

    relevance_score: Mapped[int] = mapped_column(Integer)
    intent: Mapped[LeadIntent] = mapped_column(Enum(LeadIntent))
    sentiment: Mapped[str] = mapped_column(String(50))  # positive, negative, neutral, frustrated
    priority: Mapped[LeadPriority] = mapped_column(Enum(LeadPriority))

    suggested_reply: Mapped[str] = mapped_column(Text)
    edited_reply: Mapped[str | None] = mapped_column(Text)  # 人工编辑后的版本
    status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus), default=LeadStatus.pending_review)
    published_url: Mapped[str | None] = mapped_column(Text)

    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

- [ ] **Step 2: 创建 Keyword 模型**

```python
# models/keyword.py
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from models.lead import Base


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    term: Mapped[str] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(10))  # en, zh
    platforms: Mapped[str] = mapped_column(Text)  # JSON array: ["reddit", "hackernews"]
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 3: 初始化 Alembic + 生成 migration**

```bash
cd backend
alembic init alembic
# 编辑 alembic/env.py 引入 models
alembic revision --autogenerate -m "init leads and keywords tables"
alembic upgrade head
```

- [ ] **Step 4: 验证表创建**

Run: `psql -h localhost -p 5433 -U soxbot -d soxbot -c "\dt"`
Expected: 看到 `leads` 和 `keywords` 表

- [ ] **Step 5: Commit**

```bash
git add backend/models/ backend/alembic/ backend/alembic.ini
git commit -m "feat(sox-bot): Lead + Keyword models and initial migration (SOX-200)"
```

---

### Task 3: SoxAI API 客户端 + AI 分析层（SOX-201 前半）

**Files:**
- Create: `backend/scout/__init__.py`
- Create: `backend/scout/analyzer.py`
- Create: `backend/tests/test_analyzer.py`

- [ ] **Step 1: 写 analyzer 测试**

```python
# tests/test_analyzer.py
import pytest

from scout.analyzer import ScoutAnalyzer, AnalysisResult


@pytest.fixture
def analyzer(monkeypatch):
    """使用 mock 的 SoxAI 响应创建 analyzer"""
    monkeypatch.setenv("SOXBOT_SOXAI_API_KEY", "test-key")
    return ScoutAnalyzer(api_key="test-key", base_url="https://api.soxai.io/v1")


class TestAnalyzePost:
    def test_returns_analysis_result(self, analyzer):
        result = analyzer.analyze_post(
            text="We have 30 developers and need a unified AI API gateway",
            source="reddit",
            subreddit="r/devops",
        )
        assert isinstance(result, AnalysisResult)
        assert 0 <= result.relevance_score <= 100
        assert result.intent in ("help_seeking", "complaint", "comparison", "technical", "enterprise")
        assert result.sentiment in ("positive", "negative", "neutral", "frustrated")
        assert len(result.suggested_reply) > 0

    def test_enterprise_intent_detected(self, analyzer):
        result = analyzer.analyze_post(
            text="Our team of 50 engineers needs an AI API gateway with budget controls and compliance",
            source="reddit",
            subreddit="r/devops",
        )
        assert result.intent == "enterprise"
        assert result.relevance_score >= 80

    def test_low_relevance_for_unrelated(self, analyzer):
        result = analyzer.analyze_post(
            text="Best recipe for chocolate chip cookies",
            source="reddit",
            subreddit="r/cooking",
        )
        assert result.relevance_score < 30
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && pytest tests/test_analyzer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scout'`

- [ ] **Step 3: 实现 ScoutAnalyzer**

```python
# scout/analyzer.py
from dataclasses import dataclass

from openai import OpenAI


@dataclass
class AnalysisResult:
    relevance_score: int
    intent: str
    sentiment: str
    priority: str
    suggested_reply: str


SYSTEM_PROMPT = """You are ScoutBot, an AI analyst for SoxAI — an enterprise AI API gateway.

Analyze the following social media post and return a JSON response with:
1. relevance_score (0-100): How relevant is this to AI API management, multi-model routing, team AI budgets, or API gateways?
2. intent: One of "help_seeking", "complaint", "comparison", "technical", "enterprise"
   - enterprise: mentions team size, budget, compliance, private deployment
3. sentiment: One of "positive", "negative", "neutral", "frustrated"
4. priority: "low" (score<60), "medium" (60-79), "high" (>=80 or enterprise intent)
5. suggested_reply: A helpful reply that:
   - First provides genuine value (answers the question or shares insight)
   - Naturally mentions SoxAI only if highly relevant
   - Matches the platform culture (Reddit: casual, HN: technical depth)
   - Uses developer-to-developer tone, never salesy
   - Is honest about competitors

Respond ONLY with valid JSON, no markdown."""


class ScoutAnalyzer:
    def __init__(self, api_key: str, base_url: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def analyze_post(self, text: str, source: str, subreddit: str | None = None) -> AnalysisResult:
        context = f"Platform: {source}"
        if subreddit:
            context += f", Subreddit: {subreddit}"

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"{context}\n\nPost:\n{text}"},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        import json
        data = json.loads(response.choices[0].message.content)

        return AnalysisResult(
            relevance_score=int(data["relevance_score"]),
            intent=data["intent"],
            sentiment=data["sentiment"],
            priority=data["priority"],
            suggested_reply=data["suggested_reply"],
        )
```

- [ ] **Step 4: 运行测试**

Run: `cd backend && pytest tests/test_analyzer.py -v`
Expected: 如果有真实 SoxAI API key 则 PASS，否则需要 mock（见 Step 5）

- [ ] **Step 5: 添加 mock fixture 用于 CI**

```python
# tests/conftest.py
import json
import pytest


@pytest.fixture
def mock_soxai(httpx_mock):
    """Mock SoxAI API for CI testing"""
    def _mock(relevance=85, intent="enterprise", sentiment="frustrated"):
        httpx_mock.add_response(
            url="https://api.soxai.io/v1/chat/completions",
            json={
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "relevance_score": relevance,
                            "intent": intent,
                            "sentiment": sentiment,
                            "priority": "high" if relevance >= 80 else "medium",
                            "suggested_reply": "Great question! For multi-provider routing..."
                        })
                    }
                }]
            },
        )
    return _mock
```

- [ ] **Step 6: Commit**

```bash
git add backend/scout/ backend/tests/
git commit -m "feat(sox-bot): ScoutBot AI analyzer with SoxAI API integration (SOX-201)"
```

---

### Task 4: Reddit 采集器（SOX-201 中）

**Files:**
- Create: `backend/scout/platforms/base.py`
- Create: `backend/scout/platforms/reddit.py`
- Create: `backend/tests/test_reddit_collector.py`

- [ ] **Step 1: 写 Reddit 采集器测试**

```python
# tests/test_reddit_collector.py
import pytest

from scout.platforms.base import CollectedPost
from scout.platforms.reddit import RedditCollector


class TestRedditCollector:
    def test_collect_returns_posts(self, mock_reddit):
        collector = RedditCollector(
            client_id="test",
            client_secret="test",
            username="test",
            password="test",
        )
        posts = collector.collect(keywords=["AI API gateway"], subreddits=["devops"])
        assert len(posts) > 0
        assert isinstance(posts[0], CollectedPost)
        assert posts[0].source == "reddit"

    def test_collected_post_has_required_fields(self, mock_reddit):
        collector = RedditCollector(
            client_id="test",
            client_secret="test",
            username="test",
            password="test",
        )
        posts = collector.collect(keywords=["AI API"], subreddits=["artificial"])
        post = posts[0]
        assert post.source_id  # Reddit 帖子 ID
        assert post.source_url  # permalink
        assert post.author
        assert post.text
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_reddit_collector.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 BasePlatform 和 RedditCollector**

```python
# scout/platforms/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CollectedPost:
    source: str
    source_id: str
    source_url: str
    author: str
    text: str
    subreddit: str | None = None


class BasePlatform(ABC):
    @abstractmethod
    def collect(self, keywords: list[str], **kwargs) -> list[CollectedPost]:
        ...
```

```python
# scout/platforms/reddit.py
import praw

from scout.platforms.base import BasePlatform, CollectedPost


class RedditCollector(BasePlatform):
    def __init__(self, client_id: str, client_secret: str, username: str, password: str):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent="sox.bot/0.1 ScoutBot",
        )

    def collect(self, keywords: list[str], subreddits: list[str] | None = None) -> list[CollectedPost]:
        target_subs = subreddits or ["artificial", "LocalLLaMA", "devops", "machinelearning"]
        posts: list[CollectedPost] = []

        for sub_name in target_subs:
            subreddit = self.reddit.subreddit(sub_name)
            for keyword in keywords:
                for submission in subreddit.search(keyword, sort="new", time_filter="day", limit=10):
                    text = submission.title
                    if submission.selftext:
                        text += "\n\n" + submission.selftext
                    posts.append(
                        CollectedPost(
                            source="reddit",
                            source_id=submission.id,
                            source_url=f"https://reddit.com{submission.permalink}",
                            author=str(submission.author),
                            text=text,
                            subreddit=sub_name,
                        )
                    )
        return posts
```

- [ ] **Step 4: 添加 mock_reddit fixture**

```python
# tests/conftest.py — 追加
@pytest.fixture
def mock_reddit(monkeypatch):
    """Mock praw.Reddit for testing"""
    class FakeSubmission:
        id = "abc123"
        title = "Need an AI API gateway for our team"
        selftext = "We have 30 developers using multiple AI providers..."
        permalink = "/r/devops/comments/abc123/need_an_ai_api_gateway/"
        author = "enterprise_dev"

    class FakeSubreddit:
        def search(self, query, **kwargs):
            return [FakeSubmission()]

    class FakeReddit:
        def __init__(self, **kwargs):
            pass
        def subreddit(self, name):
            return FakeSubreddit()

    monkeypatch.setattr("praw.Reddit", FakeReddit)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_reddit_collector.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/scout/platforms/
git commit -m "feat(sox-bot): Reddit collector with BasePlatform abstraction (SOX-201)"
```

---

### Task 5: HackerNews 采集器（SOX-201 中）

**Files:**
- Create: `backend/scout/platforms/hackernews.py`
- Create: `backend/tests/test_hn_collector.py`

- [ ] **Step 1: 写 HN 采集器测试**

```python
# tests/test_hn_collector.py
import pytest

from scout.platforms.base import CollectedPost
from scout.platforms.hackernews import HNCollector


class TestHNCollector:
    def test_collect_returns_posts(self, mock_hn_api):
        collector = HNCollector()
        posts = collector.collect(keywords=["AI API gateway"])
        assert len(posts) > 0
        assert isinstance(posts[0], CollectedPost)
        assert posts[0].source == "hackernews"
        assert "ycombinator.com" in posts[0].source_url

    def test_includes_comments(self, mock_hn_api):
        collector = HNCollector()
        posts = collector.collect(keywords=["AI API"])
        # HN 搜索返回帖子和评论
        assert any(p.text for p in posts)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_hn_collector.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 HNCollector**

```python
# scout/platforms/hackernews.py
import httpx

from scout.platforms.base import BasePlatform, CollectedPost

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"


class HNCollector(BasePlatform):
    def __init__(self):
        self.client = httpx.Client(timeout=30)

    def collect(self, keywords: list[str], **kwargs) -> list[CollectedPost]:
        posts: list[CollectedPost] = []
        for keyword in keywords:
            resp = self.client.get(
                HN_SEARCH_URL,
                params={
                    "query": keyword,
                    "tags": "(story,comment)",
                    "numericFilters": "created_at_i>%d" % (int(__import__("time").time()) - 86400),
                    "hitsPerPage": 20,
                },
            )
            resp.raise_for_status()
            for hit in resp.json().get("hits", []):
                text = hit.get("title", "") or ""
                if hit.get("story_text"):
                    text += "\n\n" + hit["story_text"]
                if hit.get("comment_text"):
                    text = hit["comment_text"]

                object_id = hit.get("objectID", "")
                posts.append(
                    CollectedPost(
                        source="hackernews",
                        source_id=object_id,
                        source_url=f"https://news.ycombinator.com/item?id={object_id}",
                        author=hit.get("author", "unknown"),
                        text=text,
                    )
                )
        return posts
```

- [ ] **Step 4: 添加 mock_hn_api fixture**

```python
# tests/conftest.py — 追加
@pytest.fixture
def mock_hn_api(httpx_mock):
    httpx_mock.add_response(
        url=httpx.URL("https://hn.algolia.com/api/v1/search_by_date").copy_merge_params({
            "query": "AI API gateway",
            "tags": "(story,comment)",
        }),
        json={
            "hits": [{
                "objectID": "12345",
                "title": "Show HN: AI API gateway with failover",
                "story_text": "Built a gateway for routing between providers...",
                "author": "hn_user",
                "created_at_i": 1712900000,
            }]
        },
        is_optional=True,
    )
    # 通用 fallback
    httpx_mock.add_response(
        url="https://hn.algolia.com/api/v1/search_by_date",
        json={
            "hits": [{
                "objectID": "12345",
                "title": "Show HN: AI API gateway with failover",
                "story_text": "Built a gateway...",
                "author": "hn_user",
                "created_at_i": 1712900000,
            }]
        },
    )
```

- [ ] **Step 5: 运行测试确认通过**

Run: `pytest tests/test_hn_collector.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/scout/platforms/hackernews.py backend/tests/test_hn_collector.py
git commit -m "feat(sox-bot): HackerNews Algolia collector (SOX-201)"
```

---

### Task 6: 去重 + 过滤 + ScoutBot 引擎编排（SOX-201 后半）

**Files:**
- Create: `backend/scout/dedup.py`
- Create: `backend/scout/engine.py`
- Create: `backend/tests/test_dedup.py`

- [ ] **Step 1: 写去重测试**

```python
# tests/test_dedup.py
import pytest

from scout.dedup import Deduplicator
from scout.platforms.base import CollectedPost


class TestDeduplicator:
    def test_filters_already_seen(self):
        dedup = Deduplicator(seen_ids={"abc123"})
        posts = [
            CollectedPost(source="reddit", source_id="abc123", source_url="", author="a", text="old"),
            CollectedPost(source="reddit", source_id="def456", source_url="", author="b", text="new"),
        ]
        result = dedup.filter(posts)
        assert len(result) == 1
        assert result[0].source_id == "def456"

    def test_filters_below_threshold(self):
        dedup = Deduplicator(seen_ids=set())
        posts = [
            CollectedPost(source="reddit", source_id="a", source_url="", author="a", text="cookies recipe"),
            CollectedPost(source="reddit", source_id="b", source_url="", author="b", text="AI API gateway"),
        ]
        # 去重只检查 seen_ids，相关性过滤在 engine 层做
        result = dedup.filter(posts)
        assert len(result) == 2

    def test_removes_duplicates_within_batch(self):
        dedup = Deduplicator(seen_ids=set())
        posts = [
            CollectedPost(source="reddit", source_id="abc", source_url="", author="a", text="t1"),
            CollectedPost(source="hackernews", source_id="abc", source_url="", author="a", text="t1"),
        ]
        result = dedup.filter(posts)
        assert len(result) == 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_dedup.py -v`
Expected: FAIL

- [ ] **Step 3: 实现去重器**

```python
# scout/dedup.py
from scout.platforms.base import CollectedPost


class Deduplicator:
    def __init__(self, seen_ids: set[str]):
        self.seen_ids = seen_ids

    def filter(self, posts: list[CollectedPost]) -> list[CollectedPost]:
        result: list[CollectedPost] = []
        batch_ids: set[str] = set()
        for post in posts:
            if post.source_id in self.seen_ids:
                continue
            if post.source_id in batch_ids:
                continue
            batch_ids.add(post.source_id)
            result.append(post)
        return result
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_dedup.py -v`
Expected: PASS

- [ ] **Step 5: 实现 ScoutBot 引擎**

```python
# scout/engine.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config import settings
from models.lead import Lead, LeadIntent, LeadPriority, LeadStatus
from models.keyword import Keyword
from scout.analyzer import ScoutAnalyzer
from scout.dedup import Deduplicator
from scout.platforms.base import CollectedPost
from scout.platforms.reddit import RedditCollector
from scout.platforms.hackernews import HNCollector


class ScoutEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analyzer = ScoutAnalyzer(
            api_key=settings.soxai_api_key,
            base_url=settings.soxai_base_url,
        )
        self.collectors = self._init_collectors()

    def _init_collectors(self):
        collectors = []
        if settings.reddit_client_id:
            collectors.append(RedditCollector(
                client_id=settings.reddit_client_id,
                client_secret=settings.reddit_client_secret,
                username=settings.reddit_username,
                password=settings.reddit_password,
            ))
        collectors.append(HNCollector())
        return collectors

    async def run_scan(self) -> int:
        """运行一次完整扫描，返回新建线索数量"""
        # 1. 获取活跃关键词
        result = await self.db.execute(
            select(Keyword).where(Keyword.is_active == True)
        )
        keywords = result.scalars().all()
        en_keywords = [k.term for k in keywords if k.language == "en"]
        zh_keywords = [k.term for k in keywords if k.language == "zh"]

        # 2. 获取已知 source_ids 用于去重
        existing = await self.db.execute(select(Lead.source_id))
        seen_ids = {row[0] for row in existing.all()}
        dedup = Deduplicator(seen_ids=seen_ids)

        # 3. 采集
        all_posts: list[CollectedPost] = []
        for collector in self.collectors:
            kws = zh_keywords if hasattr(collector, "is_chinese") else en_keywords
            if not kws:
                kws = en_keywords  # fallback
            all_posts.extend(collector.collect(keywords=kws))

        # 4. 去重
        new_posts = dedup.filter(all_posts)

        # 5. AI 分析 + 过滤 + 存储
        created = 0
        for post in new_posts:
            analysis = self.analyzer.analyze_post(
                text=post.text,
                source=post.source,
                subreddit=post.subreddit,
            )
            if analysis.relevance_score < settings.scout_relevance_threshold:
                continue

            lead = Lead(
                source=post.source,
                source_id=post.source_id,
                source_url=post.source_url,
                author=post.author,
                original_text=post.text,
                subreddit=post.subreddit,
                relevance_score=analysis.relevance_score,
                intent=LeadIntent(analysis.intent),
                sentiment=analysis.sentiment,
                priority=LeadPriority(analysis.priority),
                suggested_reply=analysis.suggested_reply,
                status=LeadStatus.pending_review,
            )
            self.db.add(lead)
            created += 1

        await self.db.commit()
        return created
```

- [ ] **Step 6: Commit**

```bash
git add backend/scout/
git commit -m "feat(sox-bot): ScoutBot engine — dedup + analysis + storage pipeline (SOX-201)"
```

---

### Task 7: Celery 定时任务 + API 端点（SOX-201 完成 + SOX-202 开始）

**Files:**
- Create: `backend/tasks/celery_app.py`
- Create: `backend/schemas/lead.py`
- Create: `backend/schemas/keyword.py`
- Create: `backend/api/router.py`
- Create: `backend/api/leads.py`
- Create: `backend/api/keywords.py`
- Create: `backend/api/dashboard.py`
- Modify: `backend/main.py`

- [ ] **Step 1: 创建 Celery 定时任务**

```python
# tasks/celery_app.py
from celery import Celery
from celery.schedules import crontab

from config import settings

celery = Celery("soxbot", broker=settings.redis_url)

celery.conf.beat_schedule = {
    "scout-scan": {
        "task": "tasks.celery_app.run_scout_scan",
        "schedule": settings.scout_interval_minutes * 60,
    },
}


@celery.task
def run_scout_scan():
    """同步包装异步引擎"""
    import asyncio
    from database import async_session
    from scout.engine import ScoutEngine

    async def _scan():
        async with async_session() as db:
            engine = ScoutEngine(db)
            count = await engine.run_scan()
            return count

    count = asyncio.run(_scan())
    print(f"ScoutBot scan complete: {count} new leads")
    return count
```

- [ ] **Step 2: 创建 Pydantic schemas**

```python
# schemas/lead.py
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
```

```python
# schemas/keyword.py
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
```

- [ ] **Step 3: 创建 API 端点**

```python
# api/leads.py
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.lead import Lead, LeadStatus
from schemas.lead import LeadResponse, LeadUpdate

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("", response_model=list[LeadResponse])
async def list_leads(
    status: str | None = None,
    priority: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead).order_by(desc(Lead.detected_at)).limit(limit).offset(offset)
    if status:
        query = query.where(Lead.status == status)
    if priority:
        query = query.where(Lead.priority == priority)
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: int, body: LeadUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if body.status:
        lead.status = LeadStatus(body.status)
        if body.status == "approved":
            lead.reviewed_at = datetime.now(timezone.utc)
    if body.edited_reply is not None:
        lead.edited_reply = body.edited_reply
    await db.commit()
    await db.refresh(lead)
    return lead
```

```python
# api/keywords.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.keyword import Keyword
from schemas.keyword import KeywordCreate, KeywordResponse

router = APIRouter(prefix="/api/keywords", tags=["keywords"])


@router.get("", response_model=list[KeywordResponse])
async def list_keywords(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Keyword).order_by(Keyword.id))
    return result.scalars().all()


@router.post("", response_model=KeywordResponse, status_code=201)
async def create_keyword(body: KeywordCreate, db: AsyncSession = Depends(get_db)):
    kw = Keyword(term=body.term, language=body.language, platforms=body.platforms)
    db.add(kw)
    await db.commit()
    await db.refresh(kw)
    return kw


@router.delete("/{keyword_id}", status_code=204)
async def delete_keyword(keyword_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Keyword).where(Keyword.id == keyword_id))
    kw = result.scalar_one_or_none()
    if not kw:
        raise HTTPException(status_code=404, detail="Keyword not found")
    await db.delete(kw)
    await db.commit()
```

```python
# api/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.lead import Lead, LeadStatus, LeadPriority

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    total = await db.execute(select(func.count(Lead.id)))
    pending = await db.execute(
        select(func.count(Lead.id)).where(Lead.status == LeadStatus.pending_review)
    )
    published = await db.execute(
        select(func.count(Lead.id)).where(Lead.status == LeadStatus.published)
    )
    enterprise = await db.execute(
        select(func.count(Lead.id)).where(Lead.priority == LeadPriority.high)
    )
    return {
        "total_leads": total.scalar() or 0,
        "pending_review": pending.scalar() or 0,
        "published": published.scalar() or 0,
        "enterprise_leads": enterprise.scalar() or 0,
    }
```

```python
# api/router.py
from fastapi import APIRouter

from api.leads import router as leads_router
from api.keywords import router as keywords_router
from api.dashboard import router as dashboard_router

api_router = APIRouter()
api_router.include_router(leads_router)
api_router.include_router(keywords_router)
api_router.include_router(dashboard_router)
```

- [ ] **Step 4: 更新 main.py 注册路由**

```python
# main.py — 添加路由注册
from api.router import api_router

app.include_router(api_router)
```

- [ ] **Step 5: 写 API 端点测试**

```python
# tests/test_leads_api.py
import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_list_leads_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/leads")
        assert resp.status_code == 200
        assert resp.json() == []


@pytest.mark.asyncio
async def test_dashboard_stats():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_leads" in data
        assert "pending_review" in data
```

- [ ] **Step 6: Commit**

```bash
git add backend/tasks/ backend/schemas/ backend/api/ backend/main.py
git commit -m "feat(sox-bot): Celery tasks + REST API endpoints for leads/keywords/dashboard (SOX-201, SOX-202)"
```

---

### Task 8: 回复发布管道（SOX-202 完成）

**Files:**
- Create: `backend/publisher/manager.py`
- Create: `backend/publisher/platforms/base.py`
- Create: `backend/publisher/platforms/reddit.py`
- Create: `backend/tests/test_publisher.py`

- [ ] **Step 1: 写发布管道测试**

```python
# tests/test_publisher.py
import pytest
from unittest.mock import AsyncMock

from publisher.manager import PublishManager
from models.lead import Lead, LeadStatus


class TestPublishManager:
    @pytest.mark.asyncio
    async def test_publish_approved_lead(self):
        mock_db = AsyncMock()
        lead = Lead(
            id=1,
            source="reddit",
            source_url="https://reddit.com/r/devops/comments/abc/test",
            suggested_reply="Great question about AI API...",
            status=LeadStatus.approved,
        )
        manager = PublishManager(db=mock_db)
        manager.publishers = {"reddit": AsyncMock(return_value="https://reddit.com/r/devops/comments/abc/test/reply123")}

        result = await manager.publish(lead)
        assert result is True
        assert lead.status == LeadStatus.published
        assert lead.published_url is not None

    @pytest.mark.asyncio
    async def test_skip_non_approved_lead(self):
        mock_db = AsyncMock()
        lead = Lead(id=1, source="reddit", status=LeadStatus.pending_review)
        manager = PublishManager(db=mock_db)

        result = await manager.publish(lead)
        assert result is False
```

- [ ] **Step 2: 运行测试确认失败**

Run: `pytest tests/test_publisher.py -v`
Expected: FAIL

- [ ] **Step 3: 实现发布管道**

```python
# publisher/platforms/base.py
from abc import ABC, abstractmethod


class BasePublisher(ABC):
    @abstractmethod
    async def publish_reply(self, source_url: str, reply_text: str) -> str:
        """发布回复，返回发布后的 URL"""
        ...
```

```python
# publisher/platforms/reddit.py
import praw

from publisher.platforms.base import BasePublisher


class RedditPublisher(BasePublisher):
    def __init__(self, client_id: str, client_secret: str, username: str, password: str):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent="sox.bot/0.1 ScoutBot",
        )

    async def publish_reply(self, source_url: str, reply_text: str) -> str:
        # 从 URL 中提取帖子 ID
        # URL format: https://reddit.com/r/devops/comments/{id}/...
        parts = source_url.rstrip("/").split("/")
        submission_id = parts[parts.index("comments") + 1]
        submission = self.reddit.submission(id=submission_id)
        comment = submission.reply(reply_text)
        return f"https://reddit.com{comment.permalink}"
```

```python
# publisher/manager.py
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from models.lead import Lead, LeadStatus


class PublishManager:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.publishers: dict = {}

    async def publish(self, lead: Lead) -> bool:
        if lead.status != LeadStatus.approved:
            return False

        publisher = self.publishers.get(lead.source)
        if not publisher:
            return False

        reply_text = lead.edited_reply or lead.suggested_reply
        try:
            url = await publisher.publish_reply(lead.source_url, reply_text)
            lead.status = LeadStatus.published
            lead.published_url = url
            lead.published_at = datetime.now(timezone.utc)
            await self.db.commit()
            return True
        except Exception:
            return False
```

- [ ] **Step 4: 运行测试确认通过**

Run: `pytest tests/test_publisher.py -v`
Expected: PASS

- [ ] **Step 5: 添加发布 API 端点**

```python
# api/leads.py — 追加 publish 端点
@router.post("/{lead_id}/publish")
async def publish_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.status != LeadStatus.approved:
        raise HTTPException(status_code=400, detail="Lead must be approved before publishing")

    from publisher.manager import PublishManager
    manager = PublishManager(db=db)
    # 初始化 publishers 略（从 config 读取）
    success = await manager.publish(lead)
    if not success:
        raise HTTPException(status_code=500, detail="Publish failed")
    return {"status": "published", "url": lead.published_url}
```

- [ ] **Step 6: Commit**

```bash
git add backend/publisher/ backend/tests/test_publisher.py backend/api/leads.py
git commit -m "feat(sox-bot): publish pipeline — Reddit publisher + approval workflow (SOX-202)"
```

---

### Task 9: sox.bot Next.js 控制台（SOX-203）

**Files:**
- Create: `console/` — 完整 Next.js 项目

- [ ] **Step 1: 初始化 Next.js 项目**

```bash
cd sox-bot
bunx create-next-app@latest console --ts --tailwind --app --src-dir --no-import-alias
cd console
bunx shadcn@latest init -d
bunx shadcn@latest add button card badge table input textarea dialog tabs
```

- [ ] **Step 2: 创建 API 客户端**

```typescript
// src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8090";

export async function fetchLeads(params?: { status?: string; priority?: string }) {
  const url = new URL(`${API_BASE}/api/leads`);
  if (params?.status) url.searchParams.set("status", params.status);
  if (params?.priority) url.searchParams.set("priority", params.priority);
  const res = await fetch(url.toString());
  return res.json();
}

export async function updateLead(id: number, data: { status?: string; edited_reply?: string }) {
  const res = await fetch(`${API_BASE}/api/leads/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function publishLead(id: number) {
  const res = await fetch(`${API_BASE}/api/leads/${id}/publish`, { method: "POST" });
  return res.json();
}

export async function fetchDashboardStats() {
  const res = await fetch(`${API_BASE}/api/dashboard/stats`);
  return res.json();
}

export async function fetchKeywords() {
  const res = await fetch(`${API_BASE}/api/keywords`);
  return res.json();
}

export async function createKeyword(data: { term: string; language: string }) {
  const res = await fetch(`${API_BASE}/api/keywords`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function deleteKeyword(id: number) {
  await fetch(`${API_BASE}/api/keywords/${id}`, { method: "DELETE" });
}
```

- [ ] **Step 3: 创建 Dashboard 页面**

```tsx
// src/app/dashboard/page.tsx
"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchDashboardStats } from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState({
    total_leads: 0,
    pending_review: 0,
    published: 0,
    enterprise_leads: 0,
  });

  useEffect(() => {
    fetchDashboardStats().then(setStats);
  }, []);

  const cards = [
    { title: "待审核", value: stats.pending_review, color: "text-yellow-400" },
    { title: "已发布", value: stats.published, color: "text-green-400" },
    { title: "企业线索", value: stats.enterprise_leads, color: "text-red-400" },
    { title: "总线索", value: stats.total_leads, color: "text-blue-400" },
  ];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">sox.bot Dashboard</h1>
      <div className="grid grid-cols-4 gap-4">
        {cards.map((card) => (
          <Card key={card.title} className="bg-zinc-900 border-zinc-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-zinc-400">{card.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className={`text-3xl font-bold ${card.color}`}>{card.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: 创建 Scout 审核页面**

```tsx
// src/app/scout/page.tsx
"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { fetchLeads, updateLead, publishLead } from "@/lib/api";

interface Lead {
  id: number;
  source: string;
  source_url: string;
  author: string;
  original_text: string;
  relevance_score: number;
  intent: string;
  sentiment: string;
  priority: string;
  suggested_reply: string;
  edited_reply: string | null;
  status: string;
}

export default function ScoutPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editText, setEditText] = useState("");

  useEffect(() => {
    fetchLeads({ status: "pending_review" }).then(setLeads);
  }, []);

  const handleApprove = async (lead: Lead) => {
    await updateLead(lead.id, { status: "approved" });
    await publishLead(lead.id);
    setLeads((prev) => prev.filter((l) => l.id !== lead.id));
  };

  const handleDismiss = async (id: number) => {
    await updateLead(id, { status: "dismissed" });
    setLeads((prev) => prev.filter((l) => l.id !== id));
  };

  const handleEditSave = async (id: number) => {
    await updateLead(id, { edited_reply: editText, status: "approved" });
    await publishLead(id);
    setLeads((prev) => prev.filter((l) => l.id !== id));
    setEditingId(null);
  };

  const priorityColor: Record<string, string> = {
    high: "bg-red-600",
    medium: "bg-yellow-600",
    low: "bg-zinc-600",
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">ScoutBot - 线索审核</h1>
      <div className="space-y-4">
        {leads.map((lead) => (
          <Card key={lead.id} className="bg-zinc-900 border-zinc-800">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div className="flex items-center gap-2">
                <Badge variant="outline">{lead.source}</Badge>
                <Badge className={priorityColor[lead.priority]}>{lead.priority}</Badge>
                <Badge variant="outline">{lead.intent}</Badge>
                <span className="text-sm text-zinc-400">Score: {lead.relevance_score}</span>
              </div>
              <a href={lead.source_url} target="_blank" className="text-sm text-blue-400 hover:underline">
                @{lead.author}
              </a>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-zinc-800 rounded p-3">
                <p className="text-sm text-zinc-300 whitespace-pre-wrap">{lead.original_text}</p>
              </div>

              {editingId === lead.id ? (
                <div className="space-y-2">
                  <Textarea
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    rows={6}
                    className="bg-zinc-800"
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => handleEditSave(lead.id)}>Save & Publish</Button>
                    <Button size="sm" variant="outline" onClick={() => setEditingId(null)}>Cancel</Button>
                  </div>
                </div>
              ) : (
                <div className="bg-zinc-800/50 rounded p-3 border border-zinc-700">
                  <p className="text-xs text-zinc-500 mb-1">AI 建议回复:</p>
                  <p className="text-sm text-zinc-300 whitespace-pre-wrap">{lead.suggested_reply}</p>
                </div>
              )}

              <div className="flex gap-2">
                <Button size="sm" className="bg-green-600 hover:bg-green-700" onClick={() => handleApprove(lead)}>
                  Publish
                </Button>
                <Button size="sm" variant="outline" onClick={() => { setEditingId(lead.id); setEditText(lead.suggested_reply); }}>
                  Edit
                </Button>
                <Button size="sm" variant="ghost" className="text-red-400" onClick={() => handleDismiss(lead.id)}>
                  Dismiss
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {leads.length === 0 && (
          <p className="text-zinc-500 text-center py-12">No pending leads. ScoutBot is scanning...</p>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 5: 创建 Layout + 侧边栏导航**

```tsx
// src/app/layout.tsx
import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "sox.bot",
  description: "AI-powered community operations",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-zinc-950 text-zinc-100 flex min-h-screen">
        <aside className="w-56 bg-zinc-900 border-r border-zinc-800 p-4">
          <h2 className="text-lg font-bold text-green-400 mb-6">sox.bot</h2>
          <nav className="space-y-2">
            <Link href="/dashboard" className="block px-3 py-2 rounded hover:bg-zinc-800 text-zinc-300">
              Dashboard
            </Link>
            <Link href="/scout" className="block px-3 py-2 rounded hover:bg-zinc-800 text-zinc-300">
              ScoutBot
            </Link>
          </nav>
        </aside>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
```

- [ ] **Step 6: 验证前端启动**

Run: `cd console && bun run dev`
Expected: `http://localhost:3000/dashboard` 显示统计卡片，`/scout` 显示线索列表

- [ ] **Step 7: Commit**

```bash
git add console/
git commit -m "feat(sox-bot): Next.js console — Dashboard + ScoutBot review UI (SOX-203)"
```

---

### Task 10: 种子数据 + 端到端验证（Sprint 50 收尾）

**Files:**
- Create: `backend/scripts/seed_keywords.py`

- [ ] **Step 1: 创建种子数据脚本**

```python
# scripts/seed_keywords.py
"""插入初始监控关键词"""
import asyncio
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
```

- [ ] **Step 2: 运行种子数据**

Run: `cd backend && python scripts/seed_keywords.py`
Expected: "Seeded 12 keywords"

- [ ] **Step 3: 端到端验证**

```bash
# 1. 启动后端
cd backend && uvicorn main:app --port 8090 &

# 2. 验证 API
curl http://localhost:8090/healthz
curl http://localhost:8090/api/keywords | python -m json.tool
curl http://localhost:8090/api/dashboard/stats | python -m json.tool

# 3. 手动触发一次扫描（需要 Reddit/SoxAI API key 配置）
python -c "
import asyncio
from database import async_session
from scout.engine import ScoutEngine
async def test():
    async with async_session() as db:
        engine = ScoutEngine(db)
        count = await engine.run_scan()
        print(f'Found {count} new leads')
asyncio.run(test())
"

# 4. 启动前端
cd console && bun run dev &

# 5. 打开 http://localhost:3000/scout 查看线索
```

- [ ] **Step 4: Commit + Tag**

```bash
git add 
git commit -m "feat(sox-bot): seed keywords + end-to-end validation (Sprint 50 complete)"
git tag -a sox-bot-v0.1.0 -m "sox.bot Phase 1: ScoutBot MVP"
```
