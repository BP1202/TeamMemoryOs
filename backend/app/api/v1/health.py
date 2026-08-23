from fastapi import APIRouter 

router = APIRouter()

@router.get("/")
async def health_check():
    return{
        "status": "healthy",
        "service": "TeamMemory OS Backend",
        "version": "0.1.0"
    }