from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.health import router as health_router


app = FastAPI(
    title="Bond Insight API",
    description="Bond Insight Backend API",
    version="0.1.0",
)


# Frontend CORS 설정
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


# Router 등록
app.include_router(health_router)


@app.get("/")
def root():
    return {
        "service": "Bond Insight API",
        "status": "running"
    }