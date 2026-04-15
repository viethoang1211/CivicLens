import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, CreatedAtMixin, UUIDPrimaryKey


class StepAnnotation(Base, UUIDPrimaryKey, CreatedAtMixin):
    __tablename__ = "step_annotation"

    workflow_step_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_step.id"), nullable=False
    )
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("staff_member.id"), nullable=False)
    annotation_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    target_citizen: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    workflow_step = relationship("WorkflowStep", back_populates="annotations")
    author = relationship("StaffMember")
