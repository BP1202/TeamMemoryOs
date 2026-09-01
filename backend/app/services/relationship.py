from typing import Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.entity import Entity, EntityRelationship, RelationshipType
from app.schemas.relationship import NeighborRead, RelationshipCreate
from app.schemas.entity import EntityRead


def create_relationship(
    db: Session, rel_in: RelationshipCreate
) -> EntityRelationship:
    """Create a directed typed relationship between two entities.

    Raises ``ValueError`` if source and target are identical.
    Raises ``IntegrityError`` on a duplicate (org, src, tgt, type) combination
    or if either FK is invalid — the caller handles both.
    """
    if rel_in.source_entity_id == rel_in.target_entity_id:
        raise ValueError("source_entity_id and target_entity_id must be different")

    rel = EntityRelationship(
        organization_id=rel_in.organization_id,
        source_entity_id=rel_in.source_entity_id,
        target_entity_id=rel_in.target_entity_id,
        relationship_type=rel_in.relationship_type,
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel


def get_relationship_by_id(
    db: Session, relationship_id: UUID
) -> EntityRelationship | None:
    return db.scalar(
        select(EntityRelationship).where(EntityRelationship.id == relationship_id)
    )


def list_relationships_for_entity(
    db: Session,
    entity_id: UUID,
    relationship_type: RelationshipType | None = None,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[EntityRelationship]:
    """Return all outgoing relationships whose source is *entity_id*.

    Optionally filter by ``relationship_type``.  Results are ordered by
    creation date, newest first.
    """
    stmt = (
        select(EntityRelationship)
        .where(EntityRelationship.source_entity_id == entity_id)
        .order_by(EntityRelationship.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if relationship_type is not None:
        stmt = stmt.where(EntityRelationship.relationship_type == relationship_type)
    return db.scalars(stmt).all()


def list_neighbors(
    db: Session,
    entity_id: UUID,
    organization_id: UUID,
    relationship_type: RelationshipType | None = None,
) -> list[NeighborRead]:
    """Return all entities directly connected to *entity_id* (both directions).

    Each result includes the neighbouring ``Entity``, the ``relationship_type``,
    the ``relationship_id``, and the ``direction`` ('outgoing' or 'incoming').

    Results are scoped to ``organization_id`` to enforce tenant isolation.
    Only relationships where both endpoints belong to the same organisation
    are considered (the FK constraint guarantees this at write time).
    """
    # Outgoing: entity_id is the source — neighbour is the target
    out_stmt = (
        select(EntityRelationship, Entity)
        .join(Entity, Entity.id == EntityRelationship.target_entity_id)
        .where(
            EntityRelationship.source_entity_id == entity_id,
            EntityRelationship.organization_id == organization_id,
        )
    )
    # Incoming: entity_id is the target — neighbour is the source
    in_stmt = (
        select(EntityRelationship, Entity)
        .join(Entity, Entity.id == EntityRelationship.source_entity_id)
        .where(
            EntityRelationship.target_entity_id == entity_id,
            EntityRelationship.organization_id == organization_id,
        )
    )

    if relationship_type is not None:
        out_stmt = out_stmt.where(
            EntityRelationship.relationship_type == relationship_type
        )
        in_stmt = in_stmt.where(
            EntityRelationship.relationship_type == relationship_type
        )

    neighbors: list[NeighborRead] = []

    for rel, entity in db.execute(out_stmt).all():
        neighbors.append(
            NeighborRead(
                entity=EntityRead.model_validate(entity),
                relationship_type=rel.relationship_type,
                relationship_id=rel.id,
                direction="outgoing",
            )
        )

    for rel, entity in db.execute(in_stmt).all():
        neighbors.append(
            NeighborRead(
                entity=EntityRead.model_validate(entity),
                relationship_type=rel.relationship_type,
                relationship_id=rel.id,
                direction="incoming",
            )
        )

    # Stable sort: direction first, then relationship type, then entity name
    neighbors.sort(
        key=lambda n: (n.direction, n.relationship_type.value, n.entity.name)
    )
    return neighbors
