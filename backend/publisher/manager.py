from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from models.lead import Lead, LeadStatus
from publisher.platforms.hn_http import HNHttpPublisher
from publisher.platforms.reddit_http import RedditHttpPublisher


class PublishManager:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.publishers: dict = {
            "hackernews": HNHttpPublisher(),
            "reddit": RedditHttpPublisher(),
        }

    async def publish(self, lead: Lead) -> bool:
        if lead.status != LeadStatus.approved:
            return False

        publisher = self.publishers.get(lead.source)
        if not publisher:
            return False

        reply_text = lead.edited_reply or lead.suggested_reply

        try:
            url = await publisher.publish_reply(lead.source_url, reply_text)
            if url:
                lead.status = LeadStatus.published
                lead.published_url = url
                lead.published_at = datetime.now(timezone.utc)
                await self.db.commit()
                return True
            return False
        except Exception as e:
            print(f"Publish failed for {lead.source}: {e}")
            return False
