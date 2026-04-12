# sox.bot

AI-powered community operations platform for [SoxAI](https://www.soxai.io).

Four autonomous bots that work as your marketing team:

- **ScoutBot** — monitors Reddit/HN/Twitter/Zhihu for relevant discussions, generates reply drafts
- **ContentBot** — auto-generates bilingual blog posts, tweets, social media content
- **CommunityBot** — Discord + WeChat bot with RAG-powered tech support
- **AnalyticsBot** — weekly ops reports with data-driven action recommendations

All bots use SoxAI's own multi-model API (dogfooding).

## Status

Phase 1: ScoutBot (in progress)

## Architecture

```
sox.bot Dashboard (Next.js)
        │
        ▼
  FastAPI Backend ──── Celery Workers
        │                    │
        ▼                    ▼
   PostgreSQL          SoxAI API (AI engine)
   + PGVector          Reddit/HN/Twitter APIs
```

## Quick Start

```bash
# Backend
cd backend
pip install -e ".[dev]"
docker compose up -d  # PG + Redis
alembic upgrade head
uvicorn main:app --port 8090

# Console
cd console
bun install
bun run dev
```

## Design Docs

- [Community Automation Design](docs/specs/2026-04-12-sox-bot-community-automation-design.md)
- [Phase 1 Plan: ScoutBot](docs/plans/2026-04-12-phase1-scoutbot.md)
