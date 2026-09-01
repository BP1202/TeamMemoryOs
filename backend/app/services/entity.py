from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entity import Entity, EntityType, MemoryEntity
from app.schemas.entity import EntityCreate, MemoryEntityCreate


def create_entity(db: Session, entity_in: EntityCreate) -> Entity:
    """Create a new entity.

    Raises ``IntegrityError`` if an entity with the same
    (organization_id, entity_type, name) already exists.
    """
    entity = Entity(
        organization_id=entity_in.organization_id,
        entity_type=entity_in.entity_type,
        name=entity_in.name,
        description=entity_in.description,
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


def get_or_create_entity(
    db: Session,
    organization_id: UUID,
    entity_type: EntityType,
    name: str,
    description: str | None = None,
) -> Entity:
    """Return the matching entity or create it if it does not exist.

    Avoids duplicate (org, type, name) entries by doing a lookup first.
    """
    stmt = select(Entity).where(
        Entity.organization_id == organization_id,
        Entity.entity_type == entity_type,
        Entity.name == name,
    )
    existing = db.scalar(stmt)
    if existing is not None:
        return existing
    return create_entity(
        db,
        EntityCreate(
            organization_id=organization_id,
            entity_type=entity_type,
            name=name,
            description=description,
        ),
    )


def get_entity_by_id(db: Session, entity_id: UUID) -> Entity | None:
    return db.scalar(select(Entity).where(Entity.id == entity_id))


def get_entities_by_org(
    db: Session,
    organization_id: UUID,
    entity_type: EntityType | None = None,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[Entity]:
    stmt = (
        select(Entity)
        .where(Entity.organization_id == organization_id)
        .order_by(Entity.entity_type, Entity.name)
        .offset(skip)
        .limit(limit)
    )
    if entity_type is not None:
        stmt = stmt.where(Entity.entity_type == entity_type)
    return db.scalars(stmt).all()


def attach_entity_to_memory(
    db: Session, link_in: MemoryEntityCreate
) -> MemoryEntity:
    """Attach an entity to a memory entry.

    Raises ``IntegrityError`` on duplicate attachment or unknown FK.
    """
    link = MemoryEntity(
        memory_entry_id=link_in.memory_entry_id,
        entity_id=link_in.entity_id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def get_entities_for_memory(
    db: Session, memory_entry_id: UUID
) -> Sequence[Entity]:
    """Return all entities attached to a given memory entry."""
    stmt = (
        select(Entity)
        .join(MemoryEntity, MemoryEntity.entity_id == Entity.id)
        .where(MemoryEntity.memory_entry_id == memory_entry_id)
        .order_by(Entity.entity_type, Entity.name)
    )
    return db.scalars(stmt).all()
