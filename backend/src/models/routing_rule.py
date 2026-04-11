import uuid

from sqlalchemy import ForeignKey, Integer, SmallInteger, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, UUIDPrimaryKey, CreatedAtMixin


class RoutingRule(Base, UUIDPrimaryKey, CreatedAtMixin):
    __tablename__ = "routing_rule"
    __table_args__ = (
        UniqueConstraint("document_type_id", "step_order", name="uq_routing_rule_type_step"),
        UniqueConstraint("document_type_id", "department_id", name="uq_routing_rule_type_dept"),
    )

    document_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_type.id"), nullable=False
    )
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("department.id"), nullable=False)
    step_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    expected_duration_hours: Mapped[int | None] = mapped_column(Integer)
    required_clearance_level: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")

    document_type = relationship("DocumentType", back_populates="routing_rules")
    department = relationship("Department", back_populates="routing_rules")
