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
        """Run a full scan cycle, return number of new leads created."""
        # 1. Get active keywords
        result = await self.db.execute(
            select(Keyword).where(Keyword.is_active == True)
        )
        keywords = result.scalars().all()
        en_keywords = [k.term for k in keywords if k.language == "en"]
        zh_keywords = [k.term for k in keywords if k.language == "zh"]

        # 2. Get existing source_ids for dedup
        existing = await self.db.execute(select(Lead.source_id))
        seen_ids = {row[0] for row in existing.all()}
        dedup = Deduplicator(seen_ids=seen_ids)

        # 3. Collect from all platforms
        all_posts: list[CollectedPost] = []
        for collector in self.collectors:
            kws = zh_keywords if hasattr(collector, "is_chinese") else en_keywords
            if not kws:
                kws = en_keywords
            all_posts.extend(collector.collect(keywords=kws))

        # 4. Deduplicate
        new_posts = dedup.filter(all_posts)

        # 5. Analyze + filter + store
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
