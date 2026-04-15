import uuid

from sqlalchemy import Boolean, ForeignKey, SmallInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, CreatedAtMixin, UUIDPrimaryKey


class DocumentRequirementGroup(Base, UUIDPrimaryKey, CreatedAtMixin):
    __tablename__ = "document_requirement_group"
    __table_args__ = (
        UniqueConstraint("case_type_id", "group_order", name="uq_doc_req_group_type_order"),
    )

    case_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("case_type.id"), nullable=False
    )
    group_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    case_type = relationship("CaseType", back_populates="requirement_groups")
    slots = relationship("DocumentRequirementSlot", back_populates="group")


class DocumentRequirementSlot(Base, UUIDPrimaryKey, CreatedAtMixin):
    __tablename__ = "document_requirement_slot"
    __table_args__ = (
        UniqueConstraint("group_id", "document_type_id", name="uq_doc_req_slot_group_type"),
    )

    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_requirement_group.id"), nullable=False
    )
    document_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_type.id"), nullable=False
    )
    label_override: Mapped[str | None] = mapped_column(String(255))

    group = relationship("DocumentRequirementGroup", back_populates="slots")
    document_type = relationship("DocumentType")
    dossier_documents = relationship("DossierDocument", back_populates="requirement_slot")
