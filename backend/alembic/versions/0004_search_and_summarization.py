"""Search & AI Summarization: extensions, columns, indexes

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # 2. Create immutable unaccent wrapper (required for generated columns and index expressions)
    op.execute("""
        CREATE OR REPLACE FUNCTION immutable_unaccent(text) RETURNS text AS $$
          SELECT unaccent($1);
        $$ LANGUAGE sql IMMUTABLE STRICT
    """)

    # 3. Add ai_summary columns to submission
    op.add_column("submission", sa.Column("ai_summary", sa.Text, nullable=True))
    op.add_column("submission", sa.Column("ai_summary_generated_at", sa.DateTime(timezone=True), nullable=True))

    # 4. Add ai_summary columns to dossier
    op.add_column("dossier", sa.Column("ai_summary", sa.Text, nullable=True))
    op.add_column("dossier", sa.Column("ai_summary_generated_at", sa.DateTime(timezone=True), nullable=True))

    # 5. Add search_vector generated column to scanned_page
    op.execute("""
        ALTER TABLE scanned_page ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector('simple',
                COALESCE(immutable_unaccent(ocr_corrected_text), '') || ' ' ||
                COALESCE(immutable_unaccent(ocr_raw_text), '')
            )
        ) STORED
    """)

    # 6. Create indexes
    op.execute("CREATE INDEX idx_scanned_page_search ON scanned_page USING GIN (search_vector)")
    op.execute("""
        CREATE INDEX idx_scanned_page_trgm ON scanned_page USING GiST (
            immutable_unaccent(COALESCE(ocr_corrected_text, ocr_raw_text, '')) gist_trgm_ops
        )
    """)
    op.execute("CREATE INDEX idx_submission_ai_summary ON submission (ai_summary_generated_at)")
    op.execute("""
        CREATE INDEX idx_citizen_fullname_trgm ON citizen USING GiST (
            immutable_unaccent(full_name) gist_trgm_ops
        )
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_citizen_fullname_trgm")
    op.execute("DROP INDEX IF EXISTS idx_submission_ai_summary")
    op.execute("DROP INDEX IF EXISTS idx_scanned_page_trgm")
    op.execute("DROP INDEX IF EXISTS idx_scanned_page_search")

    op.execute("ALTER TABLE scanned_page DROP COLUMN IF EXISTS search_vector")

    op.drop_column("dossier", "ai_summary_generated_at")
    op.drop_column("dossier", "ai_summary")
    op.drop_column("submission", "ai_summary_generated_at")
    op.drop_column("submission", "ai_summary")

    op.execute("DROP FUNCTION IF EXISTS immutable_unaccent(text)")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS unaccent")
