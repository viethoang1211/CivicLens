from sqlalchemy import Boolean, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, CreatedAtMixin, UUIDPrimaryKey


class Department(Base, UUIDPrimaryKey, CreatedAtMixin):
    __tablename__ = "department"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024))
    min_clearance_level: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    staff_members = relationship("StaffMember", back_populates="department")
    routing_rules = relationship("RoutingRule", back_populates="department")
