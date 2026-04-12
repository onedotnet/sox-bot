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
            CollectedPost(source="reddit", source_id="a", source_url="", author="a", text="cookies"),
            CollectedPost(source="reddit", source_id="b", source_url="", author="b", text="AI API"),
        ]
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
