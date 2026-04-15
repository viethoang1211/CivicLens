import uuid

from sqlalchemy import Boolean, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, CreatedAtMixin, UUIDPrimaryKey


class DossierDocument(Base, UUIDPrimaryKey, CreatedAtMixin):
    __tablename__ = "dossier_document"
    __table_args__ = (
        UniqueConstraint(
            "dossier_id",
            "requirement_slot_id",
            name="uq_dossier_document_dossier_slot",
        ),
    )

    dossier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dossier.id"), nullable=False)
    requirement_slot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_requirement_slot.id"), nullable=True
    )
    document_type_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_type.id"), nullable=True
    )
    ai_match_result: Mapped[dict | None] = mapped_column(JSONB)
    ai_match_overridden: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    staff_notes: Mapped[str | None] = mapped_column(Text)

    dossier = relationship("Dossier", back_populates="documents")
    requirement_slot = relationship("DocumentRequirementSlot", back_populates="dossier_documents")
    document_type = relationship("DocumentType")
    scanned_pages = relationship("ScannedPage", back_populates="dossier_document", order_by="ScannedPage.page_number")
