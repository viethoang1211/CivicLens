import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, CreatedAtMixin, TimestampMixin, UUIDPrimaryKey


class CaseType(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "case_type"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    retention_years: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    retention_permanent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    routing_steps = relationship(
        "CaseTypeRoutingStep", back_populates="case_type", order_by="CaseTypeRoutingStep.step_order"
    )
    requirement_groups = relationship(
        "DocumentRequirementGroup", back_populates="case_type", order_by="DocumentRequirementGroup.group_order"
    )
    dossiers = relationship("Dossier", back_populates="case_type")


class CaseTypeRoutingStep(Base, UUIDPrimaryKey, CreatedAtMixin):
    __tablename__ = "case_type_routing_step"
    __table_args__ = (
        UniqueConstraint("case_type_id", "step_order", name="uq_ct_routing_step_type_order"),
        UniqueConstraint("case_type_id", "department_id", name="uq_ct_routing_step_type_dept"),
    )

    case_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("case_type.id"), nullable=False
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("department.id"), nullable=False
    )
    step_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    expected_duration_hours: Mapped[int | None] = mapped_column(Integer)
    required_clearance_level: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")

    case_type = relationship("CaseType", back_populates="routing_steps")
    department = relationship("Department")
