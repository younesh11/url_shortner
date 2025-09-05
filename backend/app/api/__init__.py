from fastapi import APIRouter

from .health import router as health_router
from .shorten import router as shorten_router
from .redirect import router as redirect_router  

api_router = APIRouter()
api_router.include_router(health_router)   # /api/health
api_router.include_router(shorten_router)  # /api/shorten, /api/resolve/{code}
api_router.include_router(redirect_router)