from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.entities import router as entities_router
from app.api.v1.health import router as health_router
from app.api.v1.members import router as members_router
from app.api.v1.memory_entries import router as memory_entries_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.relationships import router as relationships_router
from app.api.v1.scenarios import router as scenarios_router
from app.api.v1.users import router as users_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(organizations_router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(members_router, prefix="/members", tags=["Members"])
api_router.include_router(scenarios_router, prefix="/scenarios", tags=["Scenarios"])
api_router.include_router(memory_entries_router, prefix="/memory", tags=["Memory"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(entities_router, prefix="/entities", tags=["Entities"])
api_router.include_router(relationships_router, prefix="/relationships", tags=["Relationships"])
