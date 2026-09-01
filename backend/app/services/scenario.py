from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.scenario import Scenario
from app.schemas.scenario import ScenarioCreate


def create_scenario(db: Session, scenario_in: ScenarioCreate) -> Scenario:
    scenario = Scenario(
        organization_id=scenario_in.organization_id,
        created_by_user_id=scenario_in.created_by_user_id,
        name=scenario_in.name,
        description=scenario_in.description,
        is_active=scenario_in.is_active,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


def get_scenario_by_id(db: Session, scenario_id: UUID) -> Scenario | None:
    return db.scalar(select(Scenario).where(Scenario.id == scenario_id))


def get_scenarios_by_org(
    db: Session, organization_id: UUID, skip: int = 0, limit: int = 100
) -> Sequence[Scenario]:
    stmt = (
        select(Scenario)
        .where(Scenario.organization_id == organization_id)
        .offset(skip)
        .limit(limit)
    )
    return db.scalars(stmt).all()
