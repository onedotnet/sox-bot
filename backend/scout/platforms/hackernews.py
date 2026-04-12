import time
import httpx
from scout.platforms.base import BasePlatform, CollectedPost

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"


class HNCollector(BasePlatform):
    def __init__(self):
        self.client = httpx.Client(timeout=30)

    def collect(self, keywords: list[str], **kwargs) -> list[CollectedPost]:
        posts: list[CollectedPost] = []
        for keyword in keywords:
            resp = self.client.get(
                HN_SEARCH_URL,
                params={
                    "query": keyword,
                    "tags": "(story,comment)",
                    "numericFilters": "created_at_i>%d" % (int(time.time()) - 86400),
                    "hitsPerPage": 20,
                },
            )
            resp.raise_for_status()
            for hit in resp.json().get("hits", []):
                text = hit.get("title", "") or ""
                if hit.get("story_text"):
                    text += "\n\n" + hit["story_text"]
                if hit.get("comment_text"):
                    text = hit["comment_text"]

                object_id = hit.get("objectID", "")
                posts.append(
                    CollectedPost(
                        source="hackernews",
                        source_id=object_id,
                        source_url=f"https://news.ycombinator.com/item?id={object_id}",
                        author=hit.get("author", "unknown"),
                        text=text,
                    )
                )
        return posts
