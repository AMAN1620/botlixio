"""knowledge_indexing_status_and_agent_tone

Revision ID: 6ae80da21dee
Revises: 12bcaf5a6d97
Create Date: 2026-04-08 21:56:00.450953

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6ae80da21dee'
down_revision: Union[str, Sequence[str], None] = '12bcaf5a6d97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

indexingstatus = sa.Enum(
    'PENDING', 'PROCESSING', 'INDEXED', 'FAILED', 'STALE',
    name='indexingstatus',
)
agenttone = sa.Enum(
    'PROFESSIONAL', 'FRIENDLY', 'CASUAL', 'EMPATHETIC',
    name='agenttone',
)


def upgrade() -> None:
    # Create enum types first
    indexingstatus.create(op.get_bind(), checkfirst=True)
    agenttone.create(op.get_bind(), checkfirst=True)

    # agent_knowledge — new columns
    op.add_column('agent_knowledge', sa.Column(
        'indexing_status', indexingstatus, nullable=False, server_default='PENDING'
    ))
    op.add_column('agent_knowledge', sa.Column('content_hash', sa.String(64), nullable=True))
    op.add_column('agent_knowledge', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('agent_knowledge', sa.Column('indexed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('agent_knowledge', sa.Column('root_url', sa.String(2048), nullable=True))
    op.add_column('agent_knowledge', sa.Column('path_filter', sa.String(255), nullable=True))
    op.add_column('agent_knowledge', sa.Column('max_pages', sa.Integer(), nullable=True))
    op.add_column('agent_knowledge', sa.Column(
        'crawled_pages', postgresql.JSONB(astext_type=sa.Text()), nullable=True
    ))

    # agents — tone column
    op.add_column('agents', sa.Column(
        'tone', agenttone, nullable=False, server_default='FRIENDLY'
    ))


def downgrade() -> None:
    op.drop_column('agents', 'tone')
    op.drop_column('agent_knowledge', 'crawled_pages')
    op.drop_column('agent_knowledge', 'max_pages')
    op.drop_column('agent_knowledge', 'path_filter')
    op.drop_column('agent_knowledge', 'root_url')
    op.drop_column('agent_knowledge', 'indexed_at')
    op.drop_column('agent_knowledge', 'error_message')
    op.drop_column('agent_knowledge', 'content_hash')
    op.drop_column('agent_knowledge', 'indexing_status')

    # Drop enum types last
    indexingstatus.drop(op.get_bind(), checkfirst=True)
    agenttone.drop(op.get_bind(), checkfirst=True)
