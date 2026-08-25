from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory_entry import MemoryEntry
from app.schemas.memory_entry import MemoryEntryCreate


def create_memory_entry(db: Session, entry_in: MemoryEntryCreate) -> MemoryEntry:
    entry = MemoryEntry(
        organization_id=entry_in.organization_id,
        scenario_id=entry_in.scenario_id,
        created_by_user_id=entry_in.created_by_user_id,
        memory_type=entry_in.memory_type,
        title=entry_in.title,
        content=entry_in.content,
        meta=entry_in.meta,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_memory_entry_by_id(db: Session, entry_id: UUID) -> MemoryEntry | None:
    return db.scalar(select(MemoryEntry).where(MemoryEntry.id == entry_id))


def get_memory_entries_by_org(
    db: Session, organization_id: UUID, skip: int = 0, limit: int = 100
) -> Sequence[MemoryEntry]:
    stmt = (
        select(MemoryEntry)
        .where(MemoryEntry.organization_id == organization_id)
        .order_by(MemoryEntry.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return db.scalars(stmt).all()


def get_memory_entries_by_scenario(
    db: Session, scenario_id: UUID, skip: int = 0, limit: int = 100
) -> Sequence[MemoryEntry]:
    stmt = (
        select(MemoryEntry)
        .where(MemoryEntry.scenario_id == scenario_id)
        .order_by(MemoryEntry.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return db.scalars(stmt).all()
