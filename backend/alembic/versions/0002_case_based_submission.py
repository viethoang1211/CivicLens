"""Case-based dossier submission: new tables and schema modifications

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- case_type ---
    op.create_table(
        "case_type",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("retention_years", sa.Integer, nullable=False, server_default="5"),
        sa.Column("retention_permanent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_case_type_is_active", "case_type", ["is_active"])

    # --- case_type_routing_step ---
    op.create_table(
        "case_type_routing_step",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("case_type_id", UUID(as_uuid=True), sa.ForeignKey("case_type.id"), nullable=False),
        sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("department.id"), nullable=False),
        sa.Column("step_order", sa.SmallInteger, nullable=False),
        sa.Column("expected_duration_hours", sa.Integer),
        sa.Column("required_clearance_level", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("case_type_id", "step_order", name="uq_ct_routing_step_type_order"),
        sa.UniqueConstraint("case_type_id", "department_id", name="uq_ct_routing_step_type_dept"),
    )

    # --- document_requirement_group ---
    op.create_table(
        "document_requirement_group",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("case_type_id", UUID(as_uuid=True), sa.ForeignKey("case_type.id"), nullable=False),
        sa.Column("group_order", sa.SmallInteger, nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("is_mandatory", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("case_type_id", "group_order", name="uq_doc_req_group_type_order"),
    )

    # --- document_requirement_slot ---
    op.create_table(
        "document_requirement_slot",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("group_id", UUID(as_uuid=True), sa.ForeignKey("document_requirement_group.id"), nullable=False),
        sa.Column("document_type_id", UUID(as_uuid=True), sa.ForeignKey("document_type.id"), nullable=False),
        sa.Column("label_override", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("group_id", "document_type_id", name="uq_doc_req_slot_group_type"),
    )

    # --- dossier ---
    op.create_table(
        "dossier",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("reference_number", sa.String(20), unique=True, nullable=True),
        sa.Column("citizen_id", UUID(as_uuid=True), sa.ForeignKey("citizen.id"), nullable=False),
        sa.Column("submitted_by_staff_id", UUID(as_uuid=True), sa.ForeignKey("staff_member.id"), nullable=False),
        sa.Column("case_type_id", UUID(as_uuid=True), sa.ForeignKey("case_type.id"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("security_classification", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("priority", sa.String(10), nullable=False, server_default="normal"),
        sa.Column("rejection_reason", sa.Text),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("retention_expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "security_classification >= 0 AND security_classification <= 3",
            name="ck_dossier_security_class",
        ),
    )
    op.create_index("idx_dossier_citizen_id", "dossier", ["citizen_id"])
    op.create_index("idx_dossier_status", "dossier", ["status"])
    op.create_index("idx_dossier_case_type_id", "dossier", ["case_type_id"])
    op.create_index(
        "idx_dossier_reference_number",
        "dossier",
        ["reference_number"],
        unique=True,
        postgresql_where=sa.text("reference_number IS NOT NULL"),
    )

    # --- dossier_document ---
    op.create_table(
        "dossier_document",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("dossier_id", UUID(as_uuid=True), sa.ForeignKey("dossier.id"), nullable=False),
        sa.Column(
            "requirement_slot_id",
            UUID(as_uuid=True),
            sa.ForeignKey("document_requirement_slot.id"),
            nullable=True,
        ),
        sa.Column("document_type_id", UUID(as_uuid=True), sa.ForeignKey("document_type.id"), nullable=True),
        sa.Column("ai_match_result", JSONB),
        sa.Column("ai_match_overridden", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("staff_notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("dossier_id", "requirement_slot_id", name="uq_dossier_document_dossier_slot"),
    )

    # --- alter scanned_page ---
    # Drop old NOT NULL constraint by altering column to nullable
    op.alter_column("scanned_page", "submission_id", nullable=True)
    # Add dossier_document_id FK
    op.add_column(
        "scanned_page",
        sa.Column("dossier_document_id", UUID(as_uuid=True), sa.ForeignKey("dossier_document.id"), nullable=True),
    )
    # Add single-owner check constraint
    op.create_check_constraint(
        "ck_scanned_page_single_owner",
        "scanned_page",
        "(submission_id IS NULL) <> (dossier_document_id IS NULL)",
    )

    # --- alter workflow_step ---
    # Drop old NOT NULL constraint by altering submission_id to nullable
    op.alter_column("workflow_step", "submission_id", nullable=True)
    # Add dossier_id FK
    op.add_column(
        "workflow_step",
        sa.Column("dossier_id", UUID(as_uuid=True), sa.ForeignKey("dossier.id"), nullable=True),
    )
    # Add unique constraint for dossier workflow steps
    op.create_unique_constraint("uq_workflow_step_dossier_order", "workflow_step", ["dossier_id", "step_order"])
    # Add single-owner check constraint
    op.create_check_constraint(
        "ck_workflow_step_single_owner",
        "workflow_step",
        "(submission_id IS NULL) <> (dossier_id IS NULL)",
    )


def downgrade() -> None:
    # Revert workflow_step changes
    op.drop_constraint("ck_workflow_step_single_owner", "workflow_step", type_="check")
    op.drop_constraint("uq_workflow_step_dossier_order", "workflow_step", type_="unique")
    op.drop_column("workflow_step", "dossier_id")
    op.alter_column("workflow_step", "submission_id", nullable=False)

    # Revert scanned_page changes
    op.drop_constraint("ck_scanned_page_single_owner", "scanned_page", type_="check")
    op.drop_column("scanned_page", "dossier_document_id")
    op.alter_column("scanned_page", "submission_id", nullable=False)

    # Drop new tables in reverse FK order
    op.drop_table("dossier_document")
    op.drop_index("idx_dossier_reference_number", "dossier")
    op.drop_index("idx_dossier_case_type_id", "dossier")
    op.drop_index("idx_dossier_status", "dossier")
    op.drop_index("idx_dossier_citizen_id", "dossier")
    op.drop_table("dossier")
    op.drop_table("document_requirement_slot")
    op.drop_table("document_requirement_group")
    op.drop_table("case_type_routing_step")
    op.drop_index("idx_case_type_is_active", "case_type")
    op.drop_table("case_type")
