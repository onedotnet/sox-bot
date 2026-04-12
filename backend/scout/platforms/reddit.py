import praw
from scout.platforms.base import BasePlatform, CollectedPost


class RedditCollector(BasePlatform):
    def __init__(self, client_id: str, client_secret: str, username: str, password: str):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent="sox.bot/0.1 ScoutBot",
        )

    def collect(self, keywords: list[str], subreddits: list[str] | None = None) -> list[CollectedPost]:
        target_subs = subreddits or ["artificial", "LocalLLaMA", "devops", "machinelearning"]
        posts: list[CollectedPost] = []
        for sub_name in target_subs:
            subreddit = self.reddit.subreddit(sub_name)
            for keyword in keywords:
                for submission in subreddit.search(keyword, sort="new", time_filter="day", limit=10):
                    text = submission.title
                    if submission.selftext:
                        text += "\n\n" + submission.selftext
                    posts.append(
                        CollectedPost(
                            source="reddit",
                            source_id=submission.id,
                            source_url=f"https://reddit.com{submission.permalink}",
                            author=str(submission.author),
                            text=text,
                            subreddit=sub_name,
                        )
                    )
        return posts
