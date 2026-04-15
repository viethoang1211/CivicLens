import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, CreatedAtMixin, UUIDPrimaryKey


class AuditLogEntry(Base, UUIDPrimaryKey, CreatedAtMixin):
    __tablename__ = "audit_log_entry"

    actor_type: Mapped[str] = mapped_column(String(10), nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(30), nullable=False)
    resource_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    clearance_check_result: Mapped[str | None] = mapped_column(String(10))
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
