#!/usr/bin/env python3
"""One-time YouTube OAuth authorization.

Run this once to authorize sox.bot to upload videos to your YouTube channel.
It will open a URL — visit it in your browser, authorize, then paste the code back.

Usage:
    python scripts/youtube_auth.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video.youtube_upload import YouTubeUploader, CLIENT_SECRET, TOKEN_FILE


def main():
    if not CLIENT_SECRET.exists():
        print("YouTube client secret not found!")
        print(f"Expected at: {CLIENT_SECRET}")
        print()
        print("Steps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create/select project → Enable YouTube Data API v3")
        print("3. Credentials → Create OAuth client ID (Desktop app)")
        print("4. Download JSON → save as:")
        print(f"   {CLIENT_SECRET}")
        sys.exit(1)

    print("Starting YouTube authorization...")
    print("A URL will be shown — open it in your browser and authorize.")
    print()

    uploader = YouTubeUploader()
    try:
        creds = uploader._get_credentials()
        print()
        print("Authorization successful!")
        print(f"Token saved to: {TOKEN_FILE}")
        print("You can now upload videos with: python scripts/youtube_upload.py")
    except Exception as e:
        print(f"Authorization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
