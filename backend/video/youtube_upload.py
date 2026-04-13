"""YouTube video uploader using OAuth2.

First-time setup:
  1. Create OAuth credentials at console.cloud.google.com
  2. Save client_secret.json to .browser-sessions/youtube_client_secret.json
  3. Run: python scripts/youtube_auth.py  (opens browser for one-time auth)
  4. After that, uploads are fully automatic

Usage:
    from video.youtube_upload import YouTubeUploader
    uploader = YouTubeUploader()
    url = uploader.upload("path/to/video.mp4", title="...", description="...")
"""

import os
import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SESSIONS_DIR = Path(__file__).parent.parent / ".browser-sessions"
CLIENT_SECRET = SESSIONS_DIR / "youtube_client_secret.json"
TOKEN_FILE = SESSIONS_DIR / "youtube_token.json"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeUploader:
    def __init__(self):
        self._service = None

    def _get_credentials(self) -> Credentials:
        """Load or refresh OAuth credentials."""
        creds = None

        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json())

        if not creds or not creds.valid:
            if not CLIENT_SECRET.exists():
                raise FileNotFoundError(
                    f"YouTube client secret not found at {CLIENT_SECRET}\n"
                    "1. Go to console.cloud.google.com → Credentials → OAuth client ID\n"
                    "2. Download JSON and save to .browser-sessions/youtube_client_secret.json\n"
                    "3. Run: python scripts/youtube_auth.py"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
            creds = flow.run_local_server(port=8099, open_browser=False)
            TOKEN_FILE.write_text(creds.to_json())

        return creds

    def _get_service(self):
        if not self._service:
            creds = self._get_credentials()
            self._service = build("youtube", "v3", credentials=creds)
        return self._service

    def upload(self, video_path: str, title: str, description: str,
               tags: list[str] | None = None,
               category_id: str = "28",  # 28 = Science & Technology
               privacy: str = "public") -> str | None:
        """Upload a video to YouTube.

        Args:
            video_path: Path to .mp4 file
            title: Video title (max 100 chars)
            description: Video description
            tags: List of tags
            category_id: YouTube category (28 = Science & Tech)
            privacy: "public", "unlisted", or "private"

        Returns:
            YouTube video URL or None on failure
        """
        if not os.path.exists(video_path):
            print(f"Video file not found: {video_path}")
            return None

        service = self._get_service()

        body = {
            "snippet": {
                "title": title[:100],
                "description": description,
                "tags": tags or ["AI", "API", "developer", "SoxAI"],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }

        # For Shorts: YouTube auto-detects vertical video < 60s
        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)

        try:
            request = service.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media,
            )

            print(f"Uploading {video_path}...")
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    print(f"  Upload {int(status.progress() * 100)}%")

            video_id = response["id"]
            url = f"https://youtube.com/watch?v={video_id}"
            print(f"Uploaded: {url}")
            return url

        except Exception as e:
            print(f"YouTube upload failed: {e}")
            return None
