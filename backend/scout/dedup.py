from scout.platforms.base import CollectedPost


class Deduplicator:
    def __init__(self, seen_ids: set[str]):
        self.seen_ids = seen_ids

    def filter(self, posts: list[CollectedPost]) -> list[CollectedPost]:
        result: list[CollectedPost] = []
        batch_ids: set[str] = set()
        for post in posts:
            if post.source_id in self.seen_ids:
                continue
            if post.source_id in batch_ids:
                continue
            batch_ids.add(post.source_id)
            result.append(post)
        return result
