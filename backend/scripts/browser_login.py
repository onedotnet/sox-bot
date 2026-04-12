#!/usr/bin/env python3
"""Login to platforms via browser for auto-publishing.

Usage:
    python scripts/browser_login.py login hn        # Login to HackerNews
    python scripts/browser_login.py login reddit     # Login to Reddit
    python scripts/browser_login.py check hn         # Check if HN session is valid
    python scripts/browser_login.py check reddit     # Check if Reddit session is valid
    python scripts/browser_login.py test hn <url>    # Test post a comment on HN
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from publisher.platforms.browser import HNPublisher, RedditPublisher


PUBLISHERS = {
    "hn": HNPublisher,
    "hackernews": HNPublisher,
    "reddit": RedditPublisher,
}


async def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]
    platform = sys.argv[2].lower()

    publisher_cls = PUBLISHERS.get(platform)
    if not publisher_cls:
        print(f"Unknown platform: {platform}. Available: {', '.join(PUBLISHERS.keys())}")
        sys.exit(1)

    publisher = publisher_cls()

    if action == "login":
        print(f"Opening browser for {platform} login...")
        print("Log in manually in the browser, then press Enter here.")
        await publisher.login_interactive()
        print("Done! Session saved. You can now auto-publish.")

    elif action == "check":
        logged_in = await publisher.is_logged_in()
        if logged_in:
            print(f"✓ {platform}: logged in, session valid")
        else:
            print(f"✗ {platform}: NOT logged in. Run: python scripts/browser_login.py login {platform}")

    elif action == "test":
        if len(sys.argv) < 4:
            print("Usage: python scripts/browser_login.py test <platform> <url>")
            sys.exit(1)
        url = sys.argv[3]
        reply = "test comment — please ignore (will delete)"
        print(f"Test posting to {url}...")
        result = await publisher.publish_reply(url, reply)
        if result:
            print(f"✓ Posted successfully: {result}")
        else:
            print("✗ Failed to post. Check if you're logged in.")

    else:
        print(f"Unknown action: {action}. Use: login, check, test")


if __name__ == "__main__":
    asyncio.run(main())
