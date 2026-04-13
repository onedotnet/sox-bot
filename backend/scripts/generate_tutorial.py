#!/usr/bin/env python3
"""Generate a tutorial video with code typing + terminal demos.

Usage:
    python scripts/generate_tutorial.py
"""
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from video.tutorial import build_tutorial, TutorialStep

# Tutorial: "Access 200+ AI Models with One API Key"
TUTORIAL_STEPS = [
    TutorialStep("text",
        text="The Problem:\n3 providers,\n3 SDKs,\n3 billing dashboards",
        narration="Most teams use multiple AI providers. That means managing multiple API keys, different SDKs, and separate billing dashboards.",
    ),

    TutorialStep("code",
        title="Step 1: Install",
        terminal_title="Terminal",
        code=[
            "$ pip install openai",
            "",
            "# That's it. No new SDK needed.",
            "# SoxAI is OpenAI-compatible.",
        ],
        narration="First, install the OpenAI SDK. That's right, you don't need a new library. SoxAI uses the same API format.",
        speed=2,
    ),

    TutorialStep("code",
        title="Step 2: Connect",
        terminal_title="app.py",
        code=[
            "from openai import OpenAI",
            "",
            "client = OpenAI(",
            '    api_key="sox-your-key",',
            '    base_url="https://api.soxai.io/v1"',
            ")",
        ],
        narration="Change two lines. Set your SoxAI API key, and point the base URL to soxai.io. Everything else stays the same.",
        speed=2,
    ),

    TutorialStep("code",
        title="Step 3: Use Any Model",
        terminal_title="app.py",
        code=[
            "# Use GPT-4o",
            "r = client.chat.completions.create(",
            '    model="gpt-4o",',
            '    messages=[{"role": "user",',
            '     "content": "Hello!"}]',
            ")",
            "",
            "# Switch to Claude — same code",
            "r = client.chat.completions.create(",
            '    model="claude-sonnet-4-20250514",',
            '    messages=[{"role": "user",',
            '     "content": "Hello!"}]',
            ")",
        ],
        narration="Now you can use any model from any provider. GPT 4 o, Claude, Gemini, DeepSeek — just change the model name. Same SDK, same code.",
        speed=2,
    ),

    TutorialStep("terminal",
        title="Step 4: Test It",
        commands=[
            {
                "cmd": 'curl https://api.soxai.io/v1/chat/completions -H "Authorization: Bearer $KEY" -d \'{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Hi"}]}\'',
                "output": '{"choices":[{"message":{"content":"Hello! How can I help?"}}]}',
            },
        ],
        narration="Let's test it with curl. One endpoint, any model. The response comes back in standard OpenAI format.",
        speed=1,
    ),

    TutorialStep("text",
        text="What you get:\n\n200+ models\nAuto failover\nTeam budgets\nPer-request costs\n\nsoxai.io",
        narration="That's it. One API key for 200 plus models, automatic failover, team budget controls, and per-request cost tracking. Try it free at soxai.io.",
    ),
]


def main():
    video_id = uuid.uuid4().hex[:8]
    output_dir = f"/tmp/sox-bot-videos/tutorial-{video_id}"
    output_path = f"{output_dir}/tutorial.mp4"

    os.makedirs(output_dir, exist_ok=True)

    result = build_tutorial(
        title="One API Key",
        subtitle="200+ AI Models",
        steps=TUTORIAL_STEPS,
        output_path=output_path,
        voice="en_casual",
    )

    if result:
        print(f"\nTutorial video: {result}")
        print("Download: scp server:{result} ~/Desktop/")
    else:
        print("Failed!")


if __name__ == "__main__":
    main()
