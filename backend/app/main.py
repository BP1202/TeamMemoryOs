from fastapi import FastAPI

from app.api.router import api_router
from app.core.logging import setup_logging
from app.core.settings import settings

logger = setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="AI Operating System for Engineering Teams"
)
app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX
)
@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return{
        "project":settings.PROJECT_NAME,
        "environment":settings.APP_ENV,
        "message":"Welcome to TeamMemory OS Backend"
    }