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

        # Mock the publisher's publish_reply method
        mock_publisher = AsyncMock()
        mock_publisher.publish_reply = AsyncMock(return_value="https://reddit.com/reply123")
        manager.publishers = {"reddit": mock_publisher}

        result = await manager.publish(lead)
        assert result is True
        assert lead.status == LeadStatus.published
        assert lead.published_url is not None

    @pytest.mark.asyncio
    async def test_skip_non_approved_lead(self):
        mock_db = AsyncMock()
        lead = Lead(id=1, source="reddit", status=LeadStatus.pending_review,
                    source_url="", suggested_reply="", source_id="x",
                    author="", original_text="", relevance_score=0,
                    intent="technical", sentiment="neutral", priority="low")
        manager = PublishManager(db=mock_db)
        result = await manager.publish(lead)
        assert result is False
