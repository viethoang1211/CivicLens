"""Add dossier_id FK to notification and submission tables

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("notification", sa.Column("dossier_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_notification_dossier_id", "notification", "dossier", ["dossier_id"], ["id"])

    op.add_column("submission", sa.Column("dossier_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_submission_dossier_id", "submission", "dossier", ["dossier_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_submission_dossier_id", "submission", type_="foreignkey")
    op.drop_column("submission", "dossier_id")

    op.drop_constraint("fk_notification_dossier_id", "notification", type_="foreignkey")
    op.drop_column("notification", "dossier_id")
