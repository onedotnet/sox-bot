from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CollectedPost:
    source: str
    source_id: str
    source_url: str
    author: str
    text: str
    subreddit: str | None = None


class BasePlatform(ABC):
    @abstractmethod
    def collect(self, keywords: list[str], **kwargs) -> list[CollectedPost]:
        ...
