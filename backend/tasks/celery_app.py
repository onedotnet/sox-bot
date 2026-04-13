import os
import sys

# Ensure backend/ is in sys.path for Celery worker subprocesses
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from celery import Celery
from celery.schedules import crontab
from config import settings

celery = Celery("soxbot", broker=settings.redis_url)

celery.conf.beat_schedule = {
    "scout-scan": {
        "task": "tasks.celery_app.run_scout_scan",
        "schedule": settings.scout_interval_minutes * 60,
    },
    "generate-weekly-plan": {
        "task": "tasks.celery_app.generate_weekly_plan_task",
        "schedule": crontab(day_of_week="sunday", hour=20, minute=0),
    },
    "weekly-report": {
        "task": "tasks.celery_app.generate_weekly_report_task",
        "schedule": crontab(day_of_week="sunday", hour=21, minute=0),
    },
}


@celery.task
def run_scout_scan():
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


@celery.task
def generate_content_task(
    keyword: str,
    content_type: str,
    language: str,
    target_platform: str,
    generate_translation: bool = False,
) -> int:
    """Generate content via the multi-model pipeline, quality-check, and save to DB."""
    import asyncio
    import json

    from database import async_session
    from content.generator import ContentGenerator
    from content.quality import QualityChecker
    from content.enricher import ContentEnricher
    from models.content import Content, ContentLanguage, ContentStatus, ContentType

    async def _generate() -> int:
        generator = ContentGenerator()
        checker = QualityChecker()
        enricher = ContentEnricher()
        try:
            result = await generator.generate(
                content_type=ContentType(content_type),
                seo_keyword=keyword,
                language=ContentLanguage(language),
                target_platform=target_platform,
            )

            # Enrich with real data (code examples, pricing, stats)
            result.body = await enricher.enrich(result.body, content_type)

            translated_body: str | None = None
            translate_model: str | None = None
            if generate_translation:
                other_lang = ContentLanguage.zh if language == "en" else ContentLanguage.en
                translated_body = await generator.translate(result.body, other_lang)
                translate_model = generator.TRANSLATE_MODEL

            quality = checker.check(
                title=result.title,
                body=result.body,
                platform=target_platform,
                language=language,
            )

            async with async_session() as db:
                content = Content(
                    title=result.title,
                    body=result.body,
                    summary=result.summary,
                    content_type=ContentType(content_type),
                    language=ContentLanguage(language),
                    status=ContentStatus.draft,
                    seo_keyword=keyword,
                    seo_tags=json.dumps(result.seo_tags),
                    outline_model=result.outline_model,
                    body_model=result.body_model,
                    translate_model=translate_model,
                    generation_cost_cents=result.cost_estimate_cents,
                    target_platform=target_platform,
                    quality_passed=quality.passed,
                    quality_notes="; ".join(quality.notes) if quality.notes else None,
                )
                db.add(content)
                await db.commit()
                await db.refresh(content)

                if translated_body is not None:
                    other_lang = ContentLanguage.zh if language == "en" else ContentLanguage.en
                    translated = Content(
                        title=result.title,
                        body=translated_body,
                        summary=result.summary,
                        content_type=ContentType(content_type),
                        language=other_lang,
                        status=ContentStatus.draft,
                        seo_keyword=keyword,
                        seo_tags=json.dumps(result.seo_tags),
                        outline_model=result.outline_model,
                        body_model=result.body_model,
                        translate_model=translate_model,
                        generation_cost_cents=0,
                        target_platform=target_platform,
                        quality_passed=False,
                        quality_notes="Translation — pending review",
                        pair_id=str(content.id),
                    )
                    db.add(translated)
                    await db.commit()

                return content.id
        finally:
            await generator.close()

    return asyncio.run(_generate())


@celery.task
def generate_weekly_plan_task() -> int:
    """Runs every Sunday 8pm UTC. Generates next week's plan from active keywords."""
    import asyncio
    from sqlalchemy import select

    from database import async_session
    from models.keyword import Keyword
    from content.calendar import ContentCalendar

    async def _plan() -> int:
        async with async_session() as db:
            result = await db.execute(
                select(Keyword).where(Keyword.is_active == True)  # noqa: E712
            )
            keywords = result.scalars().all()
            keyword_terms = [kw.term for kw in keywords] if keywords else ["AI API gateway"]

        calendar = ContentCalendar()
        next_monday = calendar.get_next_monday()
        plan = calendar.generate_weekly_plan(next_monday, keyword_terms)

        count = 0
        for slot in plan:
            generate_content_task.delay(
                keyword=slot["seo_keyword"],
                content_type=slot["content_type"],
                language=slot["language"],
                target_platform=slot["target_platform"],
                generate_translation=False,
            )
            count += 1

        print(f"Weekly plan queued: {count} content generation tasks for {next_monday.date()}")
        return count

    return asyncio.run(_plan())


@celery.task
def reindex_knowledge_task():
    """Delete all knowledge chunks and re-index from docs/**/*.md files."""
    import asyncio
    import glob
    import json
    from sqlalchemy import text
    from community.knowledge.indexer import KnowledgeIndexer
    from models.knowledge import KnowledgeChunk

    async def _reindex():
        from database import async_session
        indexer = KnowledgeIndexer(api_key=settings.soxai_api_key, base_url=settings.soxai_base_url)
        doc_files = glob.glob("docs/**/*.md", recursive=True)
        async with async_session() as db:
            await db.execute(text("DELETE FROM knowledge_chunks"))
            for filepath in doc_files:
                with open(filepath) as f:
                    content = f.read()
                chunks = indexer.chunk_markdown(content, filepath)
                if not chunks:
                    continue
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


@celery.task
def generate_weekly_report_task():
    """Runs every Sunday 9pm UTC. Aggregates the past week's metrics and generates AI report."""
    import asyncio
    import json
    from datetime import datetime, timedelta, timezone

    from analytics.aggregator import AnalyticsAggregator
    from analytics.report_generator import ReportGenerator
    from models.analytics import WeeklyReport

    async def _generate():
        from database import async_session

        now = datetime.now(timezone.utc)
        week_end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = week_end - timedelta(days=7)
        prev_start = week_start - timedelta(days=7)

        async with async_session() as db:
            agg = AnalyticsAggregator(db)
            current = await agg.aggregate_week(week_start, week_end)
            previous = await agg.aggregate_week(prev_start, week_start)

            gen = ReportGenerator()
            summary, action_items = gen.generate(current, previous)

            report = WeeklyReport(
                week_start=week_start,
                week_end=week_end,
                leads_discovered=current.leads_discovered,
                leads_published=current.leads_published,
                enterprise_leads=current.enterprise_leads,
                content_generated=current.content_generated,
                content_published=current.content_published,
                content_cost_cents=current.content_cost_cents,
                messages_received=current.messages_received,
                messages_auto_resolved=current.messages_auto_resolved,
                messages_escalated=current.messages_escalated,
                community_leads=current.community_leads,
                resolution_rate=current.resolution_rate,
                summary=summary,
                action_items=json.dumps(action_items),
            )
            db.add(report)
            await db.commit()

    asyncio.run(_generate())
    print("Weekly report generated")


@celery.task
def generate_video_task(topic: str, video_type: str = "tip",
                        language: str = "en", voice: str = "en_casual") -> str:
    """Generate a short-form video."""
    import asyncio
    from video.pipeline import VideoPipeline

    async def _gen():
        pipeline = VideoPipeline()
        result = await pipeline.generate(topic, video_type=video_type,
                                          language=language, voice=voice)
        return result["video_path"]

    path = asyncio.run(_gen())
    print(f"Video generated: {path}")
    return path


@celery.task
def generate_promo_task() -> str:
    """Generate a landscape promo video."""
    import asyncio
    import subprocess
    import uuid
    import os

    async def _gen():
        # Import and run the promo generator logic
        from scripts.generate_promo import (
            scene_title_intro, scene_problem, scene_solution,
            scene_code_demo, scene_stats, scene_cta,
            frames_to_clip, generate_audio,
        )

        video_id = uuid.uuid4().hex[:8]
        work_dir = f"/tmp/sox-bot-videos/promo-{video_id}"
        os.makedirs(work_dir, exist_ok=True)

        narrations = {
            "intro": "SoxAI. The AI API Gateway for Enterprise.",
            "problem": "Most teams use multiple AI providers. Four API keys, four billing dashboards, three different SDKs, and zero visibility.",
            "solution": "SoxAI is an OpenAI-compatible gateway. One endpoint for two hundred plus models. Automatic failover. Team budgets.",
            "code": "Two lines of code. Set your API key, point to SoxAI, done. Same SDK. Any model.",
            "stats": "Two hundred plus models. Forty plus providers. Under five milliseconds latency. Free five dollar credit.",
            "cta": "SoxAI. One API for every AI model. Start free at soxai dot io.",
        }

        audio_files = {}
        for key, text in narrations.items():
            path = f"{work_dir}/audio_{key}.mp3"
            await generate_audio(text, path, voice="en_casual", rate="-5%")
            audio_files[key] = path

        scenes = [
            ("intro", scene_title_intro),
            ("problem", scene_problem),
            ("solution", scene_solution),
            ("code", scene_code_demo),
            ("stats", scene_stats),
            ("cta", scene_cta),
        ]

        clips = []
        for i, (name, renderer) in enumerate(scenes):
            frame_dir = f"{work_dir}/{name}_frames"
            os.makedirs(frame_dir, exist_ok=True)
            frames = renderer(frame_dir)
            clip_path = f"{work_dir}/clip_{i:02d}_{name}.mp4"
            frames_to_clip(frames, audio_files.get(name), clip_path)
            clips.append(clip_path)

        concat_file = f"{work_dir}/concat.txt"
        with open(concat_file, "w") as f:
            for clip in clips:
                f.write(f"file '{clip}'\n")

        output = f"{work_dir}/soxai-promo.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file,
            "-c", "copy", output,
        ], capture_output=True)
        return output

    path = asyncio.run(_gen())
    print(f"Promo video generated: {path}")
    return path
