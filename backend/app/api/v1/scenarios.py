from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.scenario import ScenarioCreate, ScenarioRead
from app.services.scenario import (
    create_scenario,
    get_scenario_by_id,
    get_scenarios_by_org,
)

router = APIRouter()


@router.post("/", response_model=ScenarioRead, status_code=status.HTTP_201_CREATED)
def create_new_scenario(
    scenario_in: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a scenario within an organization.

    The authenticated user is recorded as the creator when
    ``created_by_user_id`` is not explicitly provided.
    """
    if scenario_in.created_by_user_id is None:
        scenario_in = scenario_in.model_copy(
            update={"created_by_user_id": current_user.id}
        )
    try:
        return create_scenario(db, scenario_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Referenced organization or user not found",
        )


@router.get("/organization/{organization_id}", response_model=List[ScenarioRead])
def list_scenarios_by_org(
    organization_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all scenarios for an organization."""
    return get_scenarios_by_org(db, organization_id, skip=skip, limit=limit)


@router.get("/{scenario_id}", response_model=ScenarioRead)
def get_scenario(
    scenario_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retrieve a single scenario by ID."""
    scenario = get_scenario_by_id(db, scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found",
        )
    return scenario
