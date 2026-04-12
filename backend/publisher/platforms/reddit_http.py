"""Reddit publisher using direct HTTP requests via old.reddit.com.

Login flow:
  1. POST https://old.reddit.com/api/login with username/password
  2. Get back reddit_session cookie + modhash token
  3. Use cookie + modhash to POST comments

Comment flow:
  1. GET the thread page to extract modhash
  2. POST to https://old.reddit.com/api/comment with cookie + modhash + text
"""

import re
import json
import httpx
from pathlib import Path

COOKIE_FILE = Path(__file__).parent.parent.parent / ".browser-sessions" / "reddit_cookie.txt"


class RedditHttpPublisher:
    """Post comments on Reddit via HTTP (old.reddit.com)."""

    def __init__(self):
        self._session_cookie = ""
        self._modhash = ""
        self._load_session()

    def _load_session(self):
        if COOKIE_FILE.exists():
            data = json.loads(COOKIE_FILE.read_text())
            self._session_cookie = data.get("cookie", "")
            self._modhash = data.get("modhash", "")

    def _save_session(self):
        COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
        COOKIE_FILE.write_text(json.dumps({
            "cookie": self._session_cookie,
            "modhash": self._modhash,
        }))

    def _headers(self) -> dict:
        return {
            "User-Agent": "sox.bot/0.1 community scout (by /u/SoxAI_Bot)",
        }

    async def login(self, username: str, password: str) -> bool:
        """Login to Reddit and save session."""
        async with httpx.AsyncClient(follow_redirects=False) as client:
            resp = await client.post(
                "https://old.reddit.com/api/login",
                data={
                    "op": "login",
                    "user": username,
                    "passwd": password,
                    "api_type": "json",
                },
                headers=self._headers(),
            )

            try:
                data = resp.json()
            except Exception:
                print(f"Reddit login failed: unexpected response")
                return False

            json_data = data.get("json", {})
            errors = json_data.get("errors", [])
            if errors:
                print(f"Reddit login failed: {errors}")
                return False

            login_data = json_data.get("data", {})
            self._modhash = login_data.get("modhash", "")
            self._session_cookie = login_data.get("cookie", "")

            # Also check Set-Cookie header
            if not self._session_cookie:
                cookie = resp.cookies.get("reddit_session")
                if cookie:
                    self._session_cookie = cookie

            if self._session_cookie and self._modhash:
                self._save_session()
                print("Reddit login successful. Session saved.")
                return True
            else:
                print("Reddit login failed — no session cookie returned")
                return False

    async def is_logged_in(self) -> bool:
        """Check if current session is valid."""
        if not self._session_cookie:
            return False
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://old.reddit.com/api/me.json",
                cookies={"reddit_session": self._session_cookie},
                headers=self._headers(),
            )
            try:
                data = resp.json()
                return bool(data.get("data", {}).get("name"))
            except Exception:
                return False

    async def _get_modhash(self, client: httpx.AsyncClient) -> str:
        """Refresh modhash from Reddit."""
        resp = await client.get(
            "https://old.reddit.com/api/me.json",
            cookies={"reddit_session": self._session_cookie},
            headers=self._headers(),
        )
        try:
            data = resp.json()
            modhash = data.get("data", {}).get("modhash", "")
            if modhash:
                self._modhash = modhash
                self._save_session()
            return modhash
        except Exception:
            return self._modhash

    async def publish_reply(self, source_url: str, reply_text: str) -> str | None:
        """Post a comment on a Reddit thread."""
        if not self._session_cookie:
            print("Not logged in to Reddit. Run: python scripts/reddit_login.py login")
            return None

        # Extract thing_id from URL
        # https://reddit.com/r/devops/comments/abc123/title/
        match = re.search(r"/comments/([a-z0-9]+)", source_url)
        if not match:
            print(f"Can't parse Reddit post ID from: {source_url}")
            return None
        post_id = match.group(1)
        thing_id = f"t3_{post_id}"  # t3_ = link/post

        async with httpx.AsyncClient(follow_redirects=True) as client:
            cookies = {"reddit_session": self._session_cookie}

            # Refresh modhash
            modhash = await self._get_modhash(client)
            if not modhash:
                print("Failed to get modhash — session might be expired")
                return None

            # POST comment
            resp = await client.post(
                "https://old.reddit.com/api/comment",
                cookies=cookies,
                headers={
                    **self._headers(),
                    "X-Modhash": modhash,
                },
                data={
                    "thing_id": thing_id,
                    "text": reply_text,
                    "api_type": "json",
                    "uh": modhash,
                },
            )

            try:
                data = resp.json()
            except Exception:
                print(f"Reddit comment failed: non-JSON response (status {resp.status_code})")
                return None

            json_data = data.get("json", {})
            errors = json_data.get("errors", [])

            if errors:
                error_msg = errors[0] if errors else "unknown"
                if any("RATELIMIT" in str(e) for e in errors):
                    print(f"Reddit rate limited: {error_msg}")
                else:
                    print(f"Reddit comment failed: {error_msg}")
                return None

            # Extract comment URL from response
            comment_data = json_data.get("data", {}).get("things", [])
            if comment_data:
                comment_id = comment_data[0].get("data", {}).get("id", "")
                if comment_id:
                    url = f"https://reddit.com/r/all/comments/{post_id}/_/{comment_id}"
                    print(f"Comment posted on Reddit: {url}")
                    return url

            # If we can't extract URL but no errors, still consider success
            print(f"Comment likely posted on Reddit post {post_id}")
            return source_url
