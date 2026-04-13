"""Video generation + upload API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/video", tags=["video"])


class VideoGenerateRequest(BaseModel):
    topic: str
    video_type: str = "tip"  # tip, code_demo, news, comparison, tutorial, promo
    language: str = "en"
    voice: str = "en_casual"


class VideoUploadRequest(BaseModel):
    video_path: str
    title: str
    description: str
    tags: list[str] = ["AI", "API", "SoxAI"]
    privacy: str = "public"


# In-memory job tracker (simple — would use DB for production)
_jobs: dict[str, dict] = {}


@router.post("/generate", status_code=202)
async def generate_video(req: VideoGenerateRequest):
    """Queue video generation via Celery."""
    from tasks.celery_app import generate_video_task
    task = generate_video_task.delay(
        topic=req.topic,
        video_type=req.video_type,
        language=req.language,
        voice=req.voice,
    )
    return {"task_id": task.id, "status": "queued"}


@router.post("/generate-promo", status_code=202)
async def generate_promo():
    """Queue landscape promo video generation."""
    from tasks.celery_app import generate_promo_task
    task = generate_promo_task.delay()
    return {"task_id": task.id, "status": "queued"}


@router.get("/list")
async def list_videos():
    """List generated videos on disk."""
    import os
    from pathlib import Path

    video_dir = Path("/tmp/sox-bot-videos")
    if not video_dir.exists():
        return []

    videos = []
    for d in sorted(video_dir.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        mp4_files = list(d.glob("*.mp4"))
        if not mp4_files:
            continue
        # Find the main video file
        main = next((f for f in mp4_files if f.name in ("final.mp4", "tutorial.mp4", "soxai-promo.mp4")), mp4_files[0])
        size = main.stat().st_size
        videos.append({
            "id": d.name,
            "filename": main.name,
            "path": str(main),
            "size_kb": size // 1024,
            "created_at": d.stat().st_mtime,
            "type": "promo" if "promo" in d.name else ("tutorial" if "tutorial" in d.name else "short"),
        })

    return videos


@router.post("/upload-youtube")
async def upload_to_youtube(req: VideoUploadRequest):
    """Upload a video to YouTube."""
    import os
    if not os.path.exists(req.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")

    from video.youtube_upload import YouTubeUploader
    uploader = YouTubeUploader()
    url = uploader.upload(
        req.video_path, req.title, req.description,
        tags=req.tags, privacy=req.privacy,
    )
    if url:
        return {"status": "uploaded", "url": url}
    raise HTTPException(status_code=500, detail="YouTube upload failed")
