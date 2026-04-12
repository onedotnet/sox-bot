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
