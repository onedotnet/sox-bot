import praw
from publisher.platforms.base import BasePublisher


class RedditPublisher(BasePublisher):
    def __init__(self, client_id: str, client_secret: str, username: str, password: str):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent="sox.bot/0.1 ScoutBot",
        )

    async def publish_reply(self, source_url: str, reply_text: str) -> str:
        parts = source_url.rstrip("/").split("/")
        submission_id = parts[parts.index("comments") + 1]
        submission = self.reddit.submission(id=submission_id)
        comment = submission.reply(reply_text)
        return f"https://reddit.com{comment.permalink}"
