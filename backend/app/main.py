from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.logging import setup_logging
from app.core.settings import settings

logger = setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="AI Operating System for Engineering Teams"
)

# Enable CORS for browser frontend requests and OPTIONS preflight
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX
)

@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {
        "project": settings.PROJECT_NAME,
        "environment": settings.APP_ENV,
        "message": "Welcome to TeamMemory OS Backend"
    }