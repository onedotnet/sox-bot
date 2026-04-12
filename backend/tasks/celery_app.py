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
    from models.content import Content, ContentLanguage, ContentStatus, ContentType

    async def _generate() -> int:
        generator = ContentGenerator()
        checker = QualityChecker()
        try:
            result = await generator.generate(
                content_type=ContentType(content_type),
                seo_keyword=keyword,
                language=ContentLanguage(language),
                target_platform=target_platform,
            )

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
