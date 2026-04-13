#!/usr/bin/env python3
"""Upload a video to YouTube.

Usage:
    python scripts/youtube_upload.py /path/to/video.mp4 "Video Title" "Description"
    python scripts/youtube_upload.py /path/to/video.mp4 "Title" "Desc" --tags "AI,API"
    python scripts/youtube_upload.py /path/to/video.mp4 "Title" "Desc" --privacy unlisted
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video.youtube_upload import YouTubeUploader


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    video_path = sys.argv[1]
    title = sys.argv[2]
    description = sys.argv[3]

    tags = ["AI", "API", "developer", "SoxAI", "LLM", "gateway"]
    privacy = "public"

    args = sys.argv[4:]
    i = 0
    while i < len(args):
        if args[i] == "--tags" and i + 1 < len(args):
            tags = args[i + 1].split(",")
            i += 2
        elif args[i] == "--privacy" and i + 1 < len(args):
            privacy = args[i + 1]
            i += 2
        else:
            i += 1

    uploader = YouTubeUploader()
    url = uploader.upload(video_path, title, description, tags=tags, privacy=privacy)

    if url:
        print(f"\nVideo live at: {url}")
    else:
        print("\nUpload failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
