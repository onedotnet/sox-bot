import pytest
from scout.platforms.base import CollectedPost
from scout.platforms.reddit import RedditCollector


@pytest.fixture
def mock_reddit(monkeypatch):
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


class TestRedditCollector:
    def test_collect_returns_posts(self, mock_reddit):
        collector = RedditCollector(client_id="t", client_secret="t", username="t", password="t")
        posts = collector.collect(keywords=["AI API gateway"], subreddits=["devops"])
        assert len(posts) > 0
        assert isinstance(posts[0], CollectedPost)
        assert posts[0].source == "reddit"

    def test_collected_post_has_required_fields(self, mock_reddit):
        collector = RedditCollector(client_id="t", client_secret="t", username="t", password="t")
        posts = collector.collect(keywords=["AI API"], subreddits=["artificial"])
        post = posts[0]
        assert post.source_id == "abc123"
        assert "reddit.com" in post.source_url
        assert post.author == "enterprise_dev"
        assert post.text
