from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin, UUIDPrimaryKey


class Citizen(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "citizen"

    vneid_subject_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    id_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(15))
    email: Mapped[str | None] = mapped_column(String(255))
    push_token: Mapped[str | None] = mapped_column(String(512))

    submissions = relationship("Submission", back_populates="citizen")
    notifications = relationship("Notification", back_populates="citizen")
    dossiers = relationship("Dossier", back_populates="citizen")
