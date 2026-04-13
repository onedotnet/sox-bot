"""End-to-end video generation pipeline.

Usage:
    from video.pipeline import VideoPipeline
    pipeline = VideoPipeline()
    result = await pipeline.generate("AI API pricing comparison 2026", video_type="comparison")
    # result = {"video_path": "/tmp/videos/...", "script": {...}, "title": "...", "description": "..."}
"""

import uuid
from pathlib import Path

from video.script_writer import ScriptWriter
from video.tts import generate_audio, generate_scene_audios
from video.renderer_ffmpeg import render_video

OUTPUT_DIR = Path("/tmp/sox-bot-videos")


class VideoPipeline:
    """Generate complete videos from a topic string."""

    def __init__(self):
        self.script_writer = ScriptWriter()

    async def generate(self, topic: str, video_type: str = "tip",
                       language: str = "en", voice: str = "en_casual") -> dict:
        """Full pipeline: script → TTS → render → output.

        Returns dict with video_path, script, title, description, tags.
        """
        video_id = uuid.uuid4().hex[:8]
        work_dir = OUTPUT_DIR / video_id
        work_dir.mkdir(parents=True, exist_ok=True)

        # 1. Generate script
        print(f"[{video_id}] Writing script for: {topic}")
        script = await self.script_writer.write(topic, video_type, language)
        print(f"[{video_id}] Script: {script.get('title', 'untitled')} ({len(script.get('scenes', []))} scenes)")

        # 2. Generate TTS for each part
        print(f"[{video_id}] Generating audio...")
        audio_files = []

        # Hook audio
        hook_path = str(work_dir / "hook.mp3")
        await generate_audio(script["hook"], hook_path, voice=voice)
        audio_files.append(hook_path)

        # Scene audios
        for i, scene in enumerate(script.get("scenes", [])):
            scene_path = str(work_dir / f"scene_{i:02d}.mp3")
            await generate_audio(scene["narration"], scene_path, voice=voice)
            audio_files.append(scene_path)

        # CTA audio
        cta_path = str(work_dir / "cta.mp3")
        await generate_audio(script.get("cta", "Try SoxAI free at soxai.io"), cta_path, voice=voice)
        audio_files.append(cta_path)

        # 3. Render video
        print(f"[{video_id}] Rendering video...")
        output_path = str(work_dir / "final.mp4")
        render_video(script, audio_files, output_path)

        print(f"[{video_id}] Video ready: {output_path}")

        return {
            "video_id": video_id,
            "video_path": output_path,
            "script": script,
            "title": script.get("title", topic),
            "description": script.get("description", ""),
            "tags": script.get("tags", []),
        }
