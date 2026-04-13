from fastapi import APIRouter
from api.leads import router as leads_router
from api.keywords import router as keywords_router
from api.dashboard import router as dashboard_router
from api.content import router as content_router
from api.calendar_api import router as calendar_router
from api.community import router as community_router
from api.analytics import router as analytics_router
from api.video import router as video_router

api_router = APIRouter()
api_router.include_router(leads_router)
api_router.include_router(keywords_router)
api_router.include_router(dashboard_router)
api_router.include_router(content_router)
api_router.include_router(calendar_router)
api_router.include_router(community_router)
api_router.include_router(analytics_router)
api_router.include_router(video_router)
