"""SQLAlchemy ORM model for the runs table."""

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.adapters.postgres.database import Base


class RunRow(Base):
    __tablename__ = "runs"

    run_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    steam_id_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    profile: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_runs_steam_id_hash", "steam_id_hash"),
        Index(
            "uq_runs_steam_profile_file",
            "steam_id_hash",
            "profile",
            "file_name",
            unique=True,
        ),
    )
