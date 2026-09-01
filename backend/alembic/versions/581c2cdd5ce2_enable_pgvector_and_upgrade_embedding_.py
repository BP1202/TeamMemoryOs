"""enable_pgvector_and_upgrade_embedding_column

Revision ID: 581c2cdd5ce2
Revises: f777c4b6c9bd
Create Date: 2026-08-26 00:00:00.000000

Creates the pgvector extension and replaces the ARRAY(Float) placeholder
on memory_entries.embedding with a proper vector(1536) column.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "581c2cdd5ce2"
down_revision: Union[str, Sequence[str], None] = "f777c4b6c9bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 1536


def upgrade() -> None:
    """Enable pgvector extension and migrate embedding column to vector type."""
    # Step 1: enable the extension (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Step 2: drop the old ARRAY(float8) placeholder column
    op.drop_column("memory_entries", "embedding")

    # Step 3: add the proper vector column
    op.add_column(
        "memory_entries",
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
    )

    # Step 4: add an HNSW index for fast approximate cosine similarity search.
    # Built now while the column is empty — zero cost, ready for when data arrives.
    op.execute(
        "CREATE INDEX ix_memory_entries_embedding_hnsw "
        "ON memory_entries "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    """Remove vector column and revert to ARRAY(float8) placeholder."""
    op.execute("DROP INDEX IF EXISTS ix_memory_entries_embedding_hnsw")
    op.drop_column("memory_entries", "embedding")
    op.add_column(
        "memory_entries",
        sa.Column(
            "embedding",
            sa.ARRAY(sa.Float()),
            nullable=True,
        ),
    )
    # Note: we intentionally do NOT drop the vector extension on downgrade
    # because other tables or tools may depend on it.
