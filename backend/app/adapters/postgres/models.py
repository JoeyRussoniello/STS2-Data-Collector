"""SQLAlchemy ORM models for raw and normalized run storage."""

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
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


class RunDataRow(Base):
    __tablename__ = "run_data"

    run_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("runs.run_id", ondelete="CASCADE"),
        primary_key=True,
    )
    win: Mapped[bool] = mapped_column(nullable=False)
    acts: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    seed: Mapped[str] = mapped_column(Text, nullable=False)
    build_id: Mapped[str] = mapped_column(Text, nullable=False)
    run_time: Mapped[int] = mapped_column(Integer, nullable=False)
    ascension: Mapped[int] = mapped_column(Integer, nullable=False)
    game_mode: Mapped[str] = mapped_column(Text, nullable=False)
    modifiers: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    start_time: Mapped[int] = mapped_column(BigInteger, nullable=False)
    was_abandoned: Mapped[bool] = mapped_column(nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    platform_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    killed_by_event: Mapped[str | None] = mapped_column(Text, nullable=True)
    killed_by_encounter: Mapped[str | None] = mapped_column(Text, nullable=True)


class RunPlayerRow(Base):
    __tablename__ = "run_players"

    run_player_id: Mapped[str] = mapped_column(String(320), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("runs.run_id", ondelete="CASCADE"),
        nullable=False,
    )
    player_id: Mapped[int] = mapped_column(Integer, nullable=False)
    character: Mapped[str] = mapped_column(Text, nullable=False)
    max_potion_slot_count: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        Index("ix_run_players_run_id", "run_id"),
        UniqueConstraint("run_id", "player_id", name="uq_run_players_run_player"),
    )


class RunCardRow(Base):
    __tablename__ = "run_cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_player_id: Mapped[str] = mapped_column(
        String(320),
        ForeignKey("run_players.run_player_id", ondelete="CASCADE"),
        nullable=False,
    )
    card_id: Mapped[str] = mapped_column(Text, nullable=False)
    floor_added_to_deck: Mapped[int] = mapped_column(Integer, nullable=False)
    current_upgrade_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enchantment: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (Index("ix_run_cards_run_player_id", "run_player_id"),)


class RunRelicRow(Base):
    __tablename__ = "run_relics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_player_id: Mapped[str] = mapped_column(
        String(320),
        ForeignKey("run_players.run_player_id", ondelete="CASCADE"),
        nullable=False,
    )
    relic_id: Mapped[str] = mapped_column(Text, nullable=False)
    floor_added_to_deck: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (Index("ix_run_relics_run_player_id", "run_player_id"),)


class RunMapPointRow(Base):
    __tablename__ = "run_map_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("runs.run_id", ondelete="CASCADE"),
        nullable=False,
    )
    map_point_index: Mapped[int] = mapped_column(Integer, nullable=False)
    map_point_type: Mapped[str] = mapped_column(Text, nullable=False)
    raw: Mapped[dict] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        Index("ix_run_map_points_run_id", "run_id"),
        UniqueConstraint("run_id", "map_point_index", name="uq_run_map_points_index"),
    )
