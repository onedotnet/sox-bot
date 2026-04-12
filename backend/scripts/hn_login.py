#!/usr/bin/env python3
"""Login to HackerNews for auto-publishing.

Usage:
    python scripts/hn_login.py login          # Login with username/password prompt
    python scripts/hn_login.py check          # Check if session is valid
    python scripts/hn_login.py test <url>     # Test posting (dry run — prints what would be posted)
"""
import asyncio
import getpass
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from publisher.platforms.hn_http import HNHttpPublisher


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]
    publisher = HNHttpPublisher()

    if action == "login":
        username = input("HN username: ")
        password = getpass.getpass("HN password: ")
        success = await publisher.login(username, password)
        if success:
            print("Login successful! You can now auto-publish to HN.")
        else:
            print("Login failed.")
            sys.exit(1)

    elif action == "check":
        logged_in = await publisher.is_logged_in()
        if logged_in:
            print("HN session valid")
        else:
            print("NOT logged in. Run: python scripts/hn_login.py login")

    elif action == "test":
        logged_in = await publisher.is_logged_in()
        if not logged_in:
            print("Not logged in. Run: python scripts/hn_login.py login")
            sys.exit(1)

        if len(sys.argv) < 3:
            print("Usage: python scripts/hn_login.py test <hn-item-url>")
            sys.exit(1)

        url = sys.argv[2]
        print(f"Would post to: {url}")
        print("(Use the API endpoint to actually post — this just verifies login)")

    else:
        print(f"Unknown action: {action}")
        print(__doc__)


if __name__ == "__main__":
    asyncio.run(main())
