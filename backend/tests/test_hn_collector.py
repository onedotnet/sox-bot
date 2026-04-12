import pytest
from scout.platforms.base import CollectedPost
from scout.platforms.hackernews import HNCollector


@pytest.fixture
def mock_hn_api(httpx_mock):
    httpx_mock.add_response(
        json={
            "hits": [{
                "objectID": "12345",
                "title": "Show HN: AI API gateway with failover",
                "story_text": "Built a gateway for routing between providers...",
                "author": "hn_user",
                "created_at_i": 1712900000,
            }]
        },
    )


class TestHNCollector:
    def test_collect_returns_posts(self, mock_hn_api):
        collector = HNCollector()
        posts = collector.collect(keywords=["AI API gateway"])
        assert len(posts) > 0
        assert isinstance(posts[0], CollectedPost)
        assert posts[0].source == "hackernews"
        assert "ycombinator.com" in posts[0].source_url

    def test_includes_story_text(self, mock_hn_api):
        collector = HNCollector()
        posts = collector.collect(keywords=["AI API"])
        assert "Built a gateway" in posts[0].text
