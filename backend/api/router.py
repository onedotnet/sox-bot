from fastapi import APIRouter
from api.leads import router as leads_router
from api.keywords import router as keywords_router
from api.dashboard import router as dashboard_router

api_router = APIRouter()
api_router.include_router(leads_router)
api_router.include_router(keywords_router)
api_router.include_router(dashboard_router)
