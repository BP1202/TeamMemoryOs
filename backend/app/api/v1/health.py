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