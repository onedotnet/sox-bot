"""HackerNews publisher using direct HTTP requests.

HN uses simple cookie-based auth + form POST for comments.
No API needed, no browser needed.

Login flow:
  1. POST https://news.ycombinator.com/login with username/password
  2. Get back a 'user' cookie
  3. Use that cookie to POST comments

Comment flow:
  1. GET the item page to extract the 'hmac' hidden field
  2. POST to https://news.ycombinator.com/comment with cookie + hmac + text
"""

import re
import httpx
from pathlib import Path

COOKIE_FILE = Path(__file__).parent.parent.parent / ".browser-sessions" / "hn_cookie.txt"


class HNHttpPublisher:
    """Post comments on HackerNews via HTTP."""

    def __init__(self, cookie: str | None = None):
        self._cookie = cookie or self._load_cookie()

    def _load_cookie(self) -> str:
        if COOKIE_FILE.exists():
            return COOKIE_FILE.read_text().strip()
        return ""

    def _save_cookie(self, cookie: str):
        COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
        COOKIE_FILE.write_text(cookie)

    async def login(self, username: str, password: str) -> bool:
        """Login to HN and save session cookie."""
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.post(
                "https://news.ycombinator.com/login",
                data={
                    "acct": username,
                    "pw": password,
                    "goto": "news",
                },
            )
            # HN sets a 'user' cookie on successful login
            user_cookie = resp.cookies.get("user")
            if user_cookie:
                self._cookie = user_cookie
                self._save_cookie(user_cookie)
                print(f"HN login successful. Cookie saved.")
                return True
            else:
                print("HN login failed — check username/password")
                return False

    async def is_logged_in(self) -> bool:
        """Check if current cookie is valid."""
        if not self._cookie:
            return False
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://news.ycombinator.com/",
                cookies={"user": self._cookie},
            )
            # If logged in, the page won't have a "login" link at top
            return 'id="logout"' in resp.text or f"user?id=" in resp.text

    async def publish_reply(self, source_url: str, reply_text: str) -> str | None:
        """Post a comment on an HN item. Returns the item URL on success."""
        if not self._cookie:
            print("Not logged in to HN. Run: python scripts/hn_login.py")
            return None

        # Extract item ID from URL
        # https://news.ycombinator.com/item?id=12345
        match = re.search(r"id=(\d+)", source_url)
        if not match:
            print(f"Can't parse HN item ID from: {source_url}")
            return None
        item_id = match.group(1)

        async with httpx.AsyncClient(follow_redirects=True) as client:
            cookies = {"user": self._cookie}

            # Step 1: GET the item page to find the hmac token
            page_resp = await client.get(
                f"https://news.ycombinator.com/item?id={item_id}",
                cookies=cookies,
            )

            # Find hmac hidden field: <input type="hidden" name="hmac" value="...">
            hmac_match = re.search(
                r'<input[^>]*name="hmac"[^>]*value="([^"]*)"', page_resp.text
            )
            if not hmac_match:
                print("Can't find hmac token — might not be logged in or page structure changed")
                return None
            hmac_value = hmac_match.group(1)

            # Also find the parent comment ID (for replies to comments vs top-level)
            # The form's 'parent' field tells HN which item we're replying to
            parent_match = re.search(
                r'<input[^>]*name="parent"[^>]*value="(\d+)"', page_resp.text
            )
            parent_id = parent_match.group(1) if parent_match else item_id

            # Step 2: POST the comment
            comment_resp = await client.post(
                "https://news.ycombinator.com/comment",
                cookies=cookies,
                data={
                    "parent": parent_id,
                    "goto": f"item?id={item_id}",
                    "hmac": hmac_value,
                    "text": reply_text,
                },
            )

            if comment_resp.status_code == 429:
                print(f"HN rate limited — wait before posting again")
                return None
            if comment_resp.status_code in (200, 302):
                # Check if the response contains an error message
                if "Please try again" in comment_resp.text or "submitting too fast" in comment_resp.text:
                    print(f"HN rate limited (soft) — try again later")
                    return None
                print(f"Comment posted on HN item {item_id}")
                return f"https://news.ycombinator.com/item?id={item_id}"
            else:
                print(f"HN comment failed: status {comment_resp.status_code}")
                return None
