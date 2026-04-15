import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, CreatedAtMixin, UUIDPrimaryKey


class ScannedPage(Base, UUIDPrimaryKey, CreatedAtMixin):
    __tablename__ = "scanned_page"
    __table_args__ = (
        UniqueConstraint("submission_id", "page_number", name="uq_scanned_page_sub_page"),
        CheckConstraint(
            "(submission_id IS NULL) <> (dossier_document_id IS NULL)",
            name="ck_scanned_page_single_owner",
        ),
    )

    submission_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submission.id"), nullable=True
    )
    dossier_document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dossier_document.id"), nullable=True
    )
    page_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    image_oss_key: Mapped[str] = mapped_column(String(512), nullable=False)
    ocr_raw_text: Mapped[str | None] = mapped_column(Text)
    ocr_corrected_text: Mapped[str | None] = mapped_column(Text)
    ocr_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4))
    image_quality_score: Mapped[float | None] = mapped_column(Numeric(5, 4))
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    search_vector = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('simple', "
            "COALESCE(immutable_unaccent(ocr_corrected_text), '') || ' ' || "
            "COALESCE(immutable_unaccent(ocr_raw_text), ''))",
            persisted=True,
        ),
    )

    submission = relationship("Submission", back_populates="scanned_pages")
    dossier_document = relationship("DossierDocument", back_populates="scanned_pages")
