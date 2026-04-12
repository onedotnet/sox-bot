#!/usr/bin/env python3
"""Login to Reddit for auto-publishing.

Usage:
    python scripts/reddit_login.py login     # Login with username/password
    python scripts/reddit_login.py check     # Check if session is valid
"""
import asyncio
import getpass
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from publisher.platforms.reddit_http import RedditHttpPublisher


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]
    publisher = RedditHttpPublisher()

    if action == "login":
        username = input("Reddit username: ")
        password = getpass.getpass("Reddit password: ")
        success = await publisher.login(username, password)
        if success:
            print("Login successful! You can now auto-publish to Reddit.")
        else:
            print("Login failed.")
            sys.exit(1)

    elif action == "check":
        logged_in = await publisher.is_logged_in()
        if logged_in:
            print("Reddit session valid")
        else:
            print("NOT logged in. Run: python scripts/reddit_login.py login")

    else:
        print(f"Unknown action: {action}")
        print(__doc__)


if __name__ == "__main__":
    asyncio.run(main())
