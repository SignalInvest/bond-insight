from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.health import router as health_router
from backend.app.config import settings


app = FastAPI(
    title=settings.app_name,
    description="Bond Insight Backend API",
    version=settings.app_version,
)


origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router)


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "status": "running"
    }