import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, UUIDPrimaryKey, TimestampMixin


class Dossier(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "dossier"
    __table_args__ = (
        CheckConstraint(
            "security_classification >= 0 AND security_classification <= 3",
            name="ck_dossier_security_class",
        ),
    )

    reference_number: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    citizen_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("citizen.id"), nullable=False)
    submitted_by_staff_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_member.id"), nullable=False
    )
    case_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("case_type.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="draft")
    security_classification: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    priority: Mapped[str] = mapped_column(String(10), nullable=False, server_default="normal")
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retention_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    citizen = relationship("Citizen", back_populates="dossiers")
    submitted_by_staff = relationship("StaffMember", foreign_keys=[submitted_by_staff_id])
    case_type = relationship("CaseType", back_populates="dossiers")
    documents = relationship("DossierDocument", back_populates="dossier")
    workflow_steps = relationship(
        "WorkflowStep",
        primaryjoin="WorkflowStep.dossier_id == Dossier.id",
        order_by="WorkflowStep.step_order",
    )
