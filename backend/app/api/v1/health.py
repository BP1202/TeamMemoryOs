from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.dependencies import get_db

router = APIRouter()


@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "service": "TeamMemory OS Backend",
        "version": "0.1.0",
    }


@router.get("/db")
def db_health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "healthy",
        "database": "connected",
    }


@router.get("/ollama")
async def ollama_health_check():
    """Verify local Ollama connectivity and configured model availability."""
    from app.providers.llm_factory import get_llm_provider
    provider = get_llm_provider("ollama")
    return await provider.acheck_health()