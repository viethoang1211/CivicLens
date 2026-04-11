"""Initial schema with all entities, indexes, and RLS policies

Revision ID: 0001
Revises:
Create Date: 2026-04-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- citizen ---
    op.create_table(
        "citizen",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("vneid_subject_id", sa.String(64), unique=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("id_number", sa.String(20), unique=True, nullable=False),
        sa.Column("phone_number", sa.String(15)),
        sa.Column("email", sa.String(255)),
        sa.Column("push_token", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- department ---
    op.create_table(
        "department",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(20), unique=True, nullable=False),
        sa.Column("description", sa.String(1024)),
        sa.Column("min_clearance_level", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- staff_member ---
    op.create_table(
        "staff_member",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("employee_id", sa.String(50), unique=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("department.id"), nullable=False),
        sa.Column("clearance_level", sa.SmallInteger, nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("password_hash", sa.String(255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("clearance_level >= 0 AND clearance_level <= 3", name="ck_clearance_level"),
    )

    # --- document_type ---
    op.create_table(
        "document_type",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("template_schema", JSONB, nullable=False),
        sa.Column("classification_prompt", sa.Text),
        sa.Column("retention_years", sa.Integer, nullable=False, server_default="5"),
        sa.Column("retention_permanent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- routing_rule ---
    op.create_table(
        "routing_rule",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("document_type_id", UUID(as_uuid=True), sa.ForeignKey("document_type.id"), nullable=False),
        sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("department.id"), nullable=False),
        sa.Column("step_order", sa.SmallInteger, nullable=False),
        sa.Column("expected_duration_hours", sa.Integer),
        sa.Column("required_clearance_level", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("document_type_id", "step_order", name="uq_routing_rule_type_step"),
        sa.UniqueConstraint("document_type_id", "department_id", name="uq_routing_rule_type_dept"),
    )

    # --- submission ---
    op.create_table(
        "submission",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("citizen_id", UUID(as_uuid=True), sa.ForeignKey("citizen.id"), nullable=False),
        sa.Column("submitted_by_staff_id", UUID(as_uuid=True), sa.ForeignKey("staff_member.id"), nullable=False),
        sa.Column("document_type_id", UUID(as_uuid=True), sa.ForeignKey("document_type.id"), nullable=True),
        sa.Column("classification_confidence", sa.Numeric(5, 4)),
        sa.Column("classification_method", sa.String(20)),
        sa.Column("security_classification", sa.SmallInteger, nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("priority", sa.String(10), nullable=False, server_default="normal"),
        sa.Column("template_data", JSONB),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("retention_expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("security_classification >= 0 AND security_classification <= 3", name="ck_security_class"),
    )

    # --- scanned_page ---
    op.create_table(
        "scanned_page",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submission.id"), nullable=False),
        sa.Column("page_number", sa.SmallInteger, nullable=False),
        sa.Column("image_oss_key", sa.String(512), nullable=False),
        sa.Column("ocr_raw_text", sa.Text),
        sa.Column("ocr_corrected_text", sa.Text),
        sa.Column("ocr_confidence", sa.Numeric(5, 4)),
        sa.Column("image_quality_score", sa.Numeric(5, 4)),
        sa.Column("synced_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("submission_id", "page_number", name="uq_scanned_page_sub_page"),
    )

    # --- workflow_step ---
    op.create_table(
        "workflow_step",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submission.id"), nullable=False),
        sa.Column("department_id", UUID(as_uuid=True), sa.ForeignKey("department.id"), nullable=False),
        sa.Column("step_order", sa.SmallInteger, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("assigned_reviewer_id", UUID(as_uuid=True), sa.ForeignKey("staff_member.id"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("expected_complete_by", sa.DateTime(timezone=True)),
        sa.Column("result", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("submission_id", "step_order", name="uq_workflow_step_sub_order"),
    )

    # --- step_annotation ---
    op.create_table(
        "step_annotation",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("workflow_step_id", UUID(as_uuid=True), sa.ForeignKey("workflow_step.id"), nullable=False),
        sa.Column("author_id", UUID(as_uuid=True), sa.ForeignKey("staff_member.id"), nullable=False),
        sa.Column("annotation_type", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("target_citizen", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- audit_log_entry ---
    op.create_table(
        "audit_log_entry",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_type", sa.String(10), nullable=False),
        sa.Column("actor_id", UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(30), nullable=False),
        sa.Column("resource_id", UUID(as_uuid=True), nullable=False),
        sa.Column("clearance_check_result", sa.String(10)),
        sa.Column("metadata", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- notification ---
    op.create_table(
        "notification",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("citizen_id", UUID(as_uuid=True), sa.ForeignKey("citizen.id"), nullable=False),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submission.id"), nullable=True),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True)),
    )

    # --- T026: Key indexes ---
    op.create_index("ix_submission_citizen_status", "submission", ["citizen_id", "status"])
    op.create_index("ix_submission_doctype_status", "submission", ["document_type_id", "status"])
    op.create_index("ix_workflow_step_sub_order", "workflow_step", ["submission_id", "step_order"])
    op.create_index("ix_workflow_step_dept_status", "workflow_step", ["department_id", "status"])
    op.create_index("ix_audit_resource", "audit_log_entry", ["resource_type", "resource_id", "created_at"])
    op.create_index("ix_audit_actor", "audit_log_entry", ["actor_id", "created_at"])

    # --- T027: Row-Level Security policies ---
    op.execute("ALTER TABLE submission ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE scanned_page ENABLE ROW LEVEL SECURITY")

    # RLS policy: staff can only access submissions at or below their clearance level
    # Uses a session variable set by the application: app.clearance_level
    op.execute("""
        CREATE POLICY submission_clearance_policy ON submission
        FOR ALL
        USING (
            security_classification <= COALESCE(current_setting('app.clearance_level', true)::int, 0)
        )
    """)

    op.execute("""
        CREATE POLICY scanned_page_clearance_policy ON scanned_page
        FOR ALL
        USING (
            submission_id IN (
                SELECT id FROM submission
                WHERE security_classification <= COALESCE(current_setting('app.clearance_level', true)::int, 0)
            )
        )
    """)

    # Bypass RLS for the application superuser role (migrations, admin)
    op.execute("ALTER TABLE submission FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE scanned_page FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS scanned_page_clearance_policy ON scanned_page")
    op.execute("DROP POLICY IF EXISTS submission_clearance_policy ON submission")
    op.execute("ALTER TABLE scanned_page DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE submission DISABLE ROW LEVEL SECURITY")

    op.drop_index("ix_audit_actor")
    op.drop_index("ix_audit_resource")
    op.drop_index("ix_workflow_step_dept_status")
    op.drop_index("ix_workflow_step_sub_order")
    op.drop_index("ix_submission_doctype_status")
    op.drop_index("ix_submission_citizen_status")

    op.drop_table("notification")
    op.drop_table("audit_log_entry")
    op.drop_table("step_annotation")
    op.drop_table("workflow_step")
    op.drop_table("scanned_page")
    op.drop_table("submission")
    op.drop_table("routing_rule")
    op.drop_table("document_type")
    op.drop_table("staff_member")
    op.drop_table("department")
    op.drop_table("citizen")
