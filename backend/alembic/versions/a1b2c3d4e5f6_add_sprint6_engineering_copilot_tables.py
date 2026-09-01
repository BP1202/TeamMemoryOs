"""add_sprint6_engineering_copilot_tables

Revision ID: a1b2c3d4e5f6
Revises: 0317f82c2c0b
Create Date: 2026-09-01 00:00:00.000000

Sprint 6 — AI Engineering Copilot tables:
* repositories
* commit_memories
* pull_requests
* pull_request_reviews
* terminal_sessions
* terminal_errors
* code_files
* code_chunks
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '0317f82c2c0b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Sprint 6 tables."""

    # -----------------------------------------------------------------------
    # repositories
    # -----------------------------------------------------------------------
    op.create_table(
        'repositories',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('remote_url', sa.String(1000), nullable=False),
        sa.Column('default_branch', sa.String(255), nullable=False, server_default='main'),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_synced_sha', sa.String(40), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'],
                                name=op.f('fk_repositories_organization_id_organizations'),
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_repositories')),
        sa.UniqueConstraint('organization_id', 'remote_url', name='uq_repositories_org_url'),
    )
    op.create_index('ix_repositories_organization_id', 'repositories', ['organization_id'], unique=False)

    # -----------------------------------------------------------------------
    # commit_memories
    # -----------------------------------------------------------------------
    op.create_table(
        'commit_memories',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('repository_id', sa.Uuid(), nullable=False),
        sa.Column('memory_entry_id', sa.Uuid(), nullable=True),
        sa.Column('commit_sha', sa.String(40), nullable=False),
        sa.Column('author_name', sa.String(255), nullable=True),
        sa.Column('author_email', sa.String(255), nullable=True),
        sa.Column('commit_message', sa.Text(), nullable=False),
        sa.Column('committed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('files_changed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('insertions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('deletions', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('changed_files', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['memory_entry_id'], ['memory_entries.id'],
                                name=op.f('fk_commit_memories_memory_entry_id_memory_entries'),
                                ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'],
                                name=op.f('fk_commit_memories_organization_id_organizations'),
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'],
                                name=op.f('fk_commit_memories_repository_id_repositories'),
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_commit_memories')),
        sa.UniqueConstraint('repository_id', 'commit_sha', name='uq_commit_memories_repo_sha'),
    )
    op.create_index('ix_commit_memories_repository_id', 'commit_memories', ['repository_id'], unique=False)
    op.create_index('ix_commit_memories_organization_id', 'commit_memories', ['organization_id'], unique=False)

    # -----------------------------------------------------------------------
    # pull_requests
    # -----------------------------------------------------------------------
    op.create_table(
        'pull_requests',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('repository_id', sa.Uuid(), nullable=False),
        sa.Column('memory_entry_id', sa.Uuid(), nullable=True),
        sa.Column('pr_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('author', sa.String(255), nullable=True),
        sa.Column('source_branch', sa.String(255), nullable=True),
        sa.Column('target_branch', sa.String(255), nullable=True),
        sa.Column('status', sa.Enum('open', 'closed', 'merged', name='prstatus'), nullable=False, server_default='open'),
        sa.Column('diff_text', sa.Text(), nullable=True),
        sa.Column('changed_files', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('files_changed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['memory_entry_id'], ['memory_entries.id'],
                                name=op.f('fk_pull_requests_memory_entry_id_memory_entries'),
                                ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'],
                                name=op.f('fk_pull_requests_organization_id_organizations'),
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'],
                                name=op.f('fk_pull_requests_repository_id_repositories'),
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_pull_requests')),
        sa.UniqueConstraint('repository_id', 'pr_number', name='uq_pull_requests_repo_number'),
    )
    op.create_index('ix_pull_requests_organization_id', 'pull_requests', ['organization_id'], unique=False)
    op.create_index('ix_pull_requests_repository_id', 'pull_requests', ['repository_id'], unique=False)

    # -----------------------------------------------------------------------
    # pull_request_reviews
    # -----------------------------------------------------------------------
    op.create_table(
        'pull_request_reviews',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('pull_request_id', sa.Uuid(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('risk_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('suggestions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'],
                                name=op.f('fk_pull_request_reviews_organization_id_organizations'),
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pull_request_id'], ['pull_requests.id'],
                                name=op.f('fk_pull_request_reviews_pull_request_id_pull_requests'),
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_pull_request_reviews')),
    )
    op.create_index('ix_pr_reviews_pull_request_id', 'pull_request_reviews', ['pull_request_id'], unique=False)
    op.create_index('ix_pr_reviews_organization_id', 'pull_request_reviews', ['organization_id'], unique=False)

    # -----------------------------------------------------------------------
    # terminal_sessions
    # -----------------------------------------------------------------------
    op.create_table(
        'terminal_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('submitted_by_user_id', sa.Uuid(), nullable=True),
        sa.Column('raw_output', sa.Text(), nullable=False),
        sa.Column('command', sa.String(1000), nullable=True),
        sa.Column('working_directory', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'],
                                name=op.f('fk_terminal_sessions_organization_id_organizations'),
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['submitted_by_user_id'], ['users.id'],
                                name=op.f('fk_terminal_sessions_submitted_by_user_id_users'),
                                ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_terminal_sessions')),
    )
    op.create_index('ix_terminal_sessions_organization_id', 'terminal_sessions', ['organization_id'], unique=False)

    # -----------------------------------------------------------------------
    # terminal_errors
    # -----------------------------------------------------------------------
    op.create_table(
        'terminal_errors',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('session_id', sa.Uuid(), nullable=False),
        sa.Column('memory_entry_id', sa.Uuid(), nullable=True),
        sa.Column('error_type', sa.String(255), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('severity', sa.Enum('low', 'medium', 'high', 'critical', name='errorseverity'), nullable=False, server_default='medium'),
        sa.Column('suggested_fixes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['memory_entry_id'], ['memory_entries.id'],
                                name=op.f('fk_terminal_errors_memory_entry_id_memory_entries'),
                                ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'],
                                name=op.f('fk_terminal_errors_organization_id_organizations'),
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['terminal_sessions.id'],
                                name=op.f('fk_terminal_errors_session_id_terminal_sessions'),
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_terminal_errors')),
    )
    op.create_index('ix_terminal_errors_organization_id', 'terminal_errors', ['organization_id'], unique=False)
    op.create_index('ix_terminal_errors_session_id', 'terminal_errors', ['session_id'], unique=False)

    # -----------------------------------------------------------------------
    # code_files
    # -----------------------------------------------------------------------
    op.create_table(
        'code_files',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('repository_id', sa.Uuid(), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('language', sa.String(50), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'],
                                name=op.f('fk_code_files_organization_id_organizations'),
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'],
                                name=op.f('fk_code_files_repository_id_repositories'),
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_code_files')),
        sa.UniqueConstraint('repository_id', 'file_path', name='uq_code_files_repo_path'),
    )
    op.create_index('ix_code_files_organization_id', 'code_files', ['organization_id'], unique=False)
    op.create_index('ix_code_files_repository_id', 'code_files', ['repository_id'], unique=False)

    # -----------------------------------------------------------------------
    # code_chunks
    # -----------------------------------------------------------------------
    op.create_table(
        'code_chunks',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('code_file_id', sa.Uuid(), nullable=False),
        sa.Column('memory_entry_id', sa.Uuid(), nullable=True),
        sa.Column('chunk_type', sa.String(50), nullable=False, server_default='block'),
        sa.Column('symbol_name', sa.String(255), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('start_line', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('end_line', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['code_file_id'], ['code_files.id'],
                                name=op.f('fk_code_chunks_code_file_id_code_files'),
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['memory_entry_id'], ['memory_entries.id'],
                                name=op.f('fk_code_chunks_memory_entry_id_memory_entries'),
                                ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'],
                                name=op.f('fk_code_chunks_organization_id_organizations'),
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_code_chunks')),
    )
    op.create_index('ix_code_chunks_organization_id', 'code_chunks', ['organization_id'], unique=False)
    op.create_index('ix_code_chunks_code_file_id', 'code_chunks', ['code_file_id'], unique=False)


def downgrade() -> None:
    """Drop Sprint 6 tables in reverse dependency order."""
    op.drop_index('ix_code_chunks_code_file_id', table_name='code_chunks')
    op.drop_index('ix_code_chunks_organization_id', table_name='code_chunks')
    op.drop_table('code_chunks')

    op.drop_index('ix_code_files_repository_id', table_name='code_files')
    op.drop_index('ix_code_files_organization_id', table_name='code_files')
    op.drop_table('code_files')

    op.drop_index('ix_terminal_errors_session_id', table_name='terminal_errors')
    op.drop_index('ix_terminal_errors_organization_id', table_name='terminal_errors')
    op.drop_table('terminal_errors')

    op.drop_index('ix_terminal_sessions_organization_id', table_name='terminal_sessions')
    op.drop_table('terminal_sessions')

    op.drop_index('ix_pr_reviews_organization_id', table_name='pull_request_reviews')
    op.drop_index('ix_pr_reviews_pull_request_id', table_name='pull_request_reviews')
    op.drop_table('pull_request_reviews')

    op.drop_index('ix_pull_requests_repository_id', table_name='pull_requests')
    op.drop_index('ix_pull_requests_organization_id', table_name='pull_requests')
    op.drop_table('pull_requests')

    op.drop_index('ix_commit_memories_organization_id', table_name='commit_memories')
    op.drop_index('ix_commit_memories_repository_id', table_name='commit_memories')
    op.drop_table('commit_memories')

    op.drop_index('ix_repositories_organization_id', table_name='repositories')
    op.drop_table('repositories')

    op.execute("DROP TYPE IF EXISTS prstatus")
    op.execute("DROP TYPE IF EXISTS errorseverity")
