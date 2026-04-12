"""Browser-based auto-publisher using Playwright.

Supports HackerNews, Reddit, Twitter, etc. by automating real browser actions.
Login once manually → session saved → subsequent posts are automatic.
"""

import asyncio
import os
import random
import time
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Persistent browser state directory
SESSIONS_DIR = Path(__file__).parent.parent.parent / ".browser-sessions"


def _human_delay(min_ms: int = 500, max_ms: int = 2000):
    """Random delay to look human."""
    return random.randint(min_ms, max_ms) / 1000


class BrowserPublisher:
    """Base class for Playwright-based publishers."""

    def __init__(self, platform: str):
        self.platform = platform
        self.session_dir = SESSIONS_DIR / platform
        self.session_dir.mkdir(parents=True, exist_ok=True)

    async def _get_context(self, playwright) -> BrowserContext:
        """Get browser context with persistent storage (cookies/localStorage)."""
        return await playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_dir),
            headless=True,
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )

    async def login_interactive(self):
        """Launch visible browser for manual login. Call once per platform."""
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(self.session_dir),
                headless=False,  # Visible so user can log in
                viewport={"width": 1280, "height": 800},
            )
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto(self._login_url())
            print(f"\n>>> Browser opened for {self.platform} login.")
            print(f">>> Log in manually, then press Enter here when done...\n")
            await asyncio.get_event_loop().run_in_executor(None, input)
            await context.close()
            print(f">>> {self.platform} session saved to {self.session_dir}")

    def _login_url(self) -> str:
        raise NotImplementedError


class HNPublisher(BrowserPublisher):
    """Auto-post comments on HackerNews."""

    def __init__(self):
        super().__init__("hackernews")

    def _login_url(self) -> str:
        return "https://news.ycombinator.com/login"

    async def is_logged_in(self) -> bool:
        async with async_playwright() as p:
            context = await self._get_context(p)
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("https://news.ycombinator.com/")
            # Check if "login" link exists (means NOT logged in)
            login_link = await page.query_selector('a[href="login"]')
            logged_in = login_link is None
            await context.close()
            return logged_in

    async def publish_reply(self, source_url: str, reply_text: str) -> str | None:
        """Post a comment on an HN thread. Returns comment URL or None on failure."""
        async with async_playwright() as p:
            context = await self._get_context(p)
            page = context.pages[0] if context.pages else await context.new_page()

            try:
                # Navigate to the HN item
                await page.goto(source_url, wait_until="domcontentloaded")
                await page.wait_for_timeout(int(_human_delay(1000, 2000) * 1000))

                # Find the comment textarea
                textarea = await page.query_selector('textarea[name="text"]')
                if not textarea:
                    print(f"No comment box found on {source_url} — might not be logged in")
                    return None

                # Type the reply with human-like delays
                await textarea.click()
                await page.wait_for_timeout(int(_human_delay(300, 800) * 1000))

                # Type character by character would be too slow, use fill but add delay before submit
                await textarea.fill(reply_text)
                await page.wait_for_timeout(int(_human_delay(2000, 4000) * 1000))

                # Click submit
                submit_btn = await page.query_selector('input[type="submit"][value="add comment"]')
                if not submit_btn:
                    print("Submit button not found")
                    return None

                await submit_btn.click()
                await page.wait_for_timeout(int(_human_delay(2000, 3000) * 1000))

                # Check if we're back on the item page (success)
                current_url = page.url
                if "news.ycombinator.com" in current_url:
                    print(f"Comment posted on {source_url}")
                    return current_url

                return None

            except Exception as e:
                print(f"HN publish error: {e}")
                return None
            finally:
                await context.close()


class RedditPublisher(BrowserPublisher):
    """Auto-post comments on Reddit via browser."""

    def __init__(self):
        super().__init__("reddit")

    def _login_url(self) -> str:
        return "https://www.reddit.com/login"

    async def is_logged_in(self) -> bool:
        async with async_playwright() as p:
            context = await self._get_context(p)
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("https://www.reddit.com/", wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            # Check for login button (means NOT logged in)
            login_btn = await page.query_selector('a[href*="login"]')
            logged_in = login_btn is None
            await context.close()
            return logged_in

    async def publish_reply(self, source_url: str, reply_text: str) -> str | None:
        """Post a comment on a Reddit thread."""
        # Use old.reddit.com for simpler HTML structure
        old_url = source_url.replace("reddit.com", "old.reddit.com")

        async with async_playwright() as p:
            context = await self._get_context(p)
            page = context.pages[0] if context.pages else await context.new_page()

            try:
                await page.goto(old_url, wait_until="domcontentloaded")
                await page.wait_for_timeout(int(_human_delay(1500, 3000) * 1000))

                # Find comment box
                textarea = await page.query_selector('textarea[name="text"]')
                if not textarea:
                    # Try new reddit
                    await page.goto(source_url, wait_until="domcontentloaded")
                    await page.wait_for_timeout(3000)
                    textarea = await page.query_selector('div[contenteditable="true"]')
                    if not textarea:
                        print(f"No comment box found on {source_url}")
                        return None

                await textarea.click()
                await page.wait_for_timeout(int(_human_delay(500, 1000) * 1000))
                await textarea.fill(reply_text)
                await page.wait_for_timeout(int(_human_delay(2000, 5000) * 1000))

                # Submit
                submit_btn = await page.query_selector('button[type="submit"].save')
                if not submit_btn:
                    submit_btn = await page.query_selector('button[slot="submit-button"]')
                if submit_btn:
                    await submit_btn.click()
                    await page.wait_for_timeout(int(_human_delay(2000, 4000) * 1000))
                    print(f"Comment posted on {source_url}")
                    return page.url
                else:
                    print("Reddit submit button not found")
                    return None

            except Exception as e:
                print(f"Reddit publish error: {e}")
                return None
            finally:
                await context.close()
