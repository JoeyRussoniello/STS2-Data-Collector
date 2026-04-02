"""add_normalized_run_tables

Revision ID: b1c4f0f8a912
Revises: 7a092709dc7b
Create Date: 2026-04-02 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b1c4f0f8a912"
down_revision: Union[str, Sequence[str], None] = "7a092709dc7b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "run_data",
        sa.Column("run_id", sa.String(length=255), nullable=False),
        sa.Column("win", sa.Boolean(), nullable=False),
        sa.Column("acts", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("seed", sa.Text(), nullable=False),
        sa.Column("build_id", sa.Text(), nullable=False),
        sa.Column("run_time", sa.Integer(), nullable=False),
        sa.Column("ascension", sa.Integer(), nullable=False),
        sa.Column("game_mode", sa.Text(), nullable=False),
        sa.Column("modifiers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("start_time", sa.BigInteger(), nullable=False),
        sa.Column("was_abandoned", sa.Boolean(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("platform_type", sa.Text(), nullable=True),
        sa.Column("killed_by_event", sa.Text(), nullable=True),
        sa.Column("killed_by_encounter", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["runs.run_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("run_id"),
    )

    op.create_table(
        "run_players",
        sa.Column("run_player_id", sa.String(length=320), nullable=False),
        sa.Column("run_id", sa.String(length=255), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("character", sa.Text(), nullable=False),
        sa.Column("max_potion_slot_count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.run_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("run_player_id"),
        sa.UniqueConstraint("run_id", "player_id", name="uq_run_players_run_player"),
    )
    op.create_index("ix_run_players_run_id", "run_players", ["run_id"], unique=False)

    op.create_table(
        "run_cards",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_player_id", sa.String(length=320), nullable=False),
        sa.Column("card_id", sa.Text(), nullable=False),
        sa.Column("floor_added_to_deck", sa.Integer(), nullable=False),
        sa.Column("current_upgrade_level", sa.Integer(), nullable=True),
        sa.Column(
            "enchantment", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["run_player_id"], ["run_players.run_player_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_run_cards_run_player_id", "run_cards", ["run_player_id"], unique=False
    )

    op.create_table(
        "run_relics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_player_id", sa.String(length=320), nullable=False),
        sa.Column("relic_id", sa.Text(), nullable=False),
        sa.Column("floor_added_to_deck", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["run_player_id"], ["run_players.run_player_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_run_relics_run_player_id", "run_relics", ["run_player_id"], unique=False
    )

    op.create_table(
        "run_map_points",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(length=255), nullable=False),
        sa.Column("map_point_index", sa.Integer(), nullable=False),
        sa.Column("map_point_type", sa.Text(), nullable=False),
        sa.Column("raw", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["runs.run_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id", "map_point_index", name="uq_run_map_points_index"
        ),
    )
    op.create_index(
        "ix_run_map_points_run_id", "run_map_points", ["run_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_run_map_points_run_id", table_name="run_map_points")
    op.drop_table("run_map_points")

    op.drop_index("ix_run_relics_run_player_id", table_name="run_relics")
    op.drop_table("run_relics")

    op.drop_index("ix_run_cards_run_player_id", table_name="run_cards")
    op.drop_table("run_cards")

    op.drop_index("ix_run_players_run_id", table_name="run_players")
    op.drop_table("run_players")

    op.drop_table("run_data")
