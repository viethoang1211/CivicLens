import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, SmallInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDPrimaryKey


class WorkflowStep(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "workflow_step"
    __table_args__ = (
        UniqueConstraint("submission_id", "step_order", name="uq_workflow_step_sub_order"),
        UniqueConstraint("dossier_id", "step_order", name="uq_workflow_step_dossier_order"),
        CheckConstraint(
            "(submission_id IS NULL) <> (dossier_id IS NULL)",
            name="ck_workflow_step_single_owner",
        ),
    )

    submission_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submission.id"), nullable=True
    )
    dossier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dossier.id"), nullable=True
    )
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("department.id"), nullable=False)
    step_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    assigned_reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_member.id"), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expected_complete_by: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    result: Mapped[str | None] = mapped_column(String(20))

    submission = relationship("Submission", back_populates="workflow_steps", foreign_keys=[submission_id])
    dossier = relationship("Dossier", foreign_keys=[dossier_id], overlaps="workflow_steps")
    department = relationship("Department")
    assigned_reviewer = relationship("StaffMember", foreign_keys=[assigned_reviewer_id])
    annotations = relationship("StepAnnotation", back_populates="workflow_step")
