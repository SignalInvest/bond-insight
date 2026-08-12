from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.health import router as health_router
from backend.app.config import settings

from backend.app.api.database import router as database_router
from backend.app.api.bonds import router as bonds_router
from backend.app.api.compare import router as compare_router
from backend.app.api.market import router as market_router
from backend.app.api.analysis import router as analysis_router
from backend.app.api.compare import post_router as compare_post_router
from backend.app.api.ai import router as ai_router
from backend.app.errors import register_error_handlers


app = FastAPI(
    title=settings.app_name,
    description="Bond Insight Backend API",
    version=settings.app_version,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)


app.include_router(health_router)
app.include_router(database_router)
app.include_router(market_router)
app.include_router(compare_router)
app.include_router(compare_post_router)
app.include_router(bonds_router)
app.include_router(analysis_router)
app.include_router(ai_router)


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "status": "running"
    }
