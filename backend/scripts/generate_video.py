#!/usr/bin/env python3
"""Generate a short-form video from a topic.

Usage:
    python scripts/generate_video.py "AI API pricing comparison 2026"
    python scripts/generate_video.py "How to use multiple AI models" --type tutorial
    python scripts/generate_video.py "GPT-5 just launched" --type news --lang zh --voice zh_male
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video.pipeline import VideoPipeline


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    topic = sys.argv[1]
    video_type = "tip"
    language = "en"
    voice = "en_casual"

    # Parse optional args
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--type" and i + 1 < len(args):
            video_type = args[i + 1]
            i += 2
        elif args[i] == "--lang" and i + 1 < len(args):
            language = args[i + 1]
            voice = f"{args[i+1]}_male"
            i += 2
        elif args[i] == "--voice" and i + 1 < len(args):
            voice = args[i + 1]
            i += 2
        else:
            i += 1

    pipeline = VideoPipeline()
    result = await pipeline.generate(topic, video_type=video_type,
                                      language=language, voice=voice)

    print(f"\nVideo generated!")
    print(f"  Path: {result['video_path']}")
    print(f"  Title: {result['title']}")
    print(f"  Tags: {', '.join(result['tags'])}")
    print(f"\nTo upload: copy the .mp4 file and upload to YouTube/TikTok")


if __name__ == "__main__":
    asyncio.run(main())
