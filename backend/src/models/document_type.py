from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, UUIDPrimaryKey, TimestampMixin


class DocumentType(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "document_type"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    template_schema: Mapped[dict] = mapped_column(JSONB, nullable=False)
    classification_prompt: Mapped[str | None] = mapped_column(Text)
    retention_years: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    retention_permanent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    routing_rules = relationship("RoutingRule", back_populates="document_type", order_by="RoutingRule.step_order")
    submissions = relationship("Submission", back_populates="document_type")
