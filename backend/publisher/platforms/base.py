from abc import ABC, abstractmethod


class BasePublisher(ABC):
    @abstractmethod
    async def publish_reply(self, source_url: str, reply_text: str) -> str:
        """Publish a reply, return the published URL"""
        ...
