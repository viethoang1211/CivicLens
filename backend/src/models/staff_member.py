import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDPrimaryKey


class StaffMember(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "staff_member"
    __table_args__ = (CheckConstraint("clearance_level >= 0 AND clearance_level <= 3", name="ck_clearance_level"),)

    employee_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("department.id"), nullable=False)
    clearance_level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, server_default="")

    department = relationship("Department", back_populates="staff_members")
