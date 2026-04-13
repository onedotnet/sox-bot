"""AI script writer for short-form video content.

Generates scripts optimized for YouTube Shorts / TikTok format:
- Hook in first 3 seconds
- One clear point per video
- Call to action at the end
"""

import json

import httpx

from config import settings


SCRIPT_PROMPT = """You write scripts for 30-60 second developer-focused video content (YouTube Shorts / TikTok).

Topic: {topic}
Type: {video_type}
Language: {language}

Return JSON with:
- "hook": First sentence to grab attention (max 10 words, provocative or surprising)
- "scenes": Array of scenes, each with:
  - "narration": What the voice says (1-2 sentences per scene)
  - "visual": What to show on screen (text overlay, code snippet, chart, or diagram description)
  - "duration": Seconds for this scene (3-8 seconds)
- "cta": Call to action (1 sentence, casual)
- "total_duration": Total seconds (target 30-60)
- "title": Video title for upload (catchy, with keywords)
- "description": Video description (2-3 sentences + link)
- "tags": Array of hashtags

RULES:
- Total duration 30-60 seconds
- 4-8 scenes max
- Each narration line must be speakable in the scene duration
- Visuals should be simple: big text, code snippets, or numbers
- Hook must create curiosity or state a surprising fact
- No corporate speak. Talk like a developer in a casual conversation.
- For code demos: show real code that works with https://api.soxai.io/v1

Output valid JSON only."""

VIDEO_TYPES = {
    "code_demo": "Quick code demo showing a specific SoxAI feature",
    "news": "AI industry news or model release commentary",
    "comparison": "Price or feature comparison between AI providers",
    "tip": "Quick developer tip about AI API usage",
    "tutorial": "Step-by-step mini tutorial",
}


class ScriptWriter:
    def __init__(self):
        self.api_key = settings.soxai_api_key
        self.base_url = settings.soxai_base_url

    async def write(self, topic: str, video_type: str = "tip",
                    language: str = "en") -> dict:
        """Generate a video script. Returns parsed JSON."""
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": "You write viral short-form video scripts. Output valid JSON only."},
                        {"role": "user", "content": SCRIPT_PROMPT.format(
                            topic=topic,
                            video_type=VIDEO_TYPES.get(video_type, video_type),
                            language=language,
                        )},
                    ],
                    "temperature": 0.8,
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)
