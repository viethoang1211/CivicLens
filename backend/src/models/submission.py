import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDPrimaryKey


class Submission(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "submission"
    __table_args__ = (
        CheckConstraint("security_classification >= 0 AND security_classification <= 3", name="ck_security_class"),
    )

    citizen_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("citizen.id"), nullable=False)
    submitted_by_staff_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_member.id"), nullable=False
    )
    document_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_type.id"), nullable=True
    )
    classification_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    classification_method: Mapped[str | None] = mapped_column(String(20))
    security_classification: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="draft")
    priority: Mapped[str] = mapped_column(String(10), nullable=False, server_default="normal")
    template_data: Mapped[dict | None] = mapped_column(JSONB)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retention_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_summary_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    dossier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dossier.id"), nullable=True
    )

    citizen = relationship("Citizen", back_populates="submissions")
    submitted_by_staff = relationship("StaffMember", foreign_keys=[submitted_by_staff_id])
    document_type = relationship("DocumentType", back_populates="submissions")
    dossier = relationship("Dossier", foreign_keys=[dossier_id])
    scanned_pages = relationship("ScannedPage", back_populates="submission", order_by="ScannedPage.page_number")
    workflow_steps = relationship("WorkflowStep", back_populates="submission", order_by="WorkflowStep.step_order")
