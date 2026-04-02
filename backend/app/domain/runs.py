from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, field_validator, model_validator


class RunData(BaseModel):
    """Flat run metadata — one row per run in the DB."""

    run_id: str
    win: bool
    acts: list[str]
    seed: str
    build_id: str
    run_time: int
    ascension: int
    game_mode: str
    modifiers: list[str] = []
    start_time: int
    was_abandoned: bool
    schema_version: int
    platform_type: Optional[str] = None
    killed_by_event: Optional[str] = None
    killed_by_encounter: Optional[str] = None

    @field_validator("killed_by_event", "killed_by_encounter")
    @classmethod
    def none_string_to_none(cls, v):
        """Replace the internal NONE.NONE used for kill events with nulls"""
        if v == "NONE.NONE":
            return None
        return v


class RunPlayer(BaseModel):
    """One row per player per run."""

    run_id: str
    player_id: int
    character: str
    max_potion_slot_count: int
    run_player_id: Optional[str] = None

    @model_validator(mode="after")
    def set_run_player_id(self) -> "RunPlayer":
        self.run_player_id = f"{self.run_id}_{self.player_id}"
        return self


class DeckItem(BaseModel):
    """Base class for items in a player's deck."""

    run_player_id: str
    id: str
    floor_added_to_deck: int


class Enchantment(BaseModel):
    id: str
    amount: int


class Card(DeckItem):
    """One row per card in a player's final deck."""

    current_upgrade_level: Optional[int] = None
    enchantment: Optional[Enchantment] = None


class Relic(DeckItem):
    """One row per relic held by a player at end of run."""

    pass


class MapPoint(BaseModel):
    """Lightweight indexed wrapper around raw map point JSON.
    Stores a few queryable fields plus the full raw data for deep dives."""

    run_id: str
    map_point_index: int
    map_point_type: str
    raw: dict


@dataclass
class ProcessedRun:
    """Container grouping all DB-ready records from a single run."""

    run_data: RunData
    players: list[RunPlayer]
    cards: list[Card]
    relics: list[Relic]
    map_points: list[MapPoint]


def process_cards(deck: list, run_player: RunPlayer) -> list[Card]:
    """Extract and validate cards from a player's deck."""
    cards = []
    for item in deck:
        card = Card(
            run_player_id=run_player.run_player_id,
            id=item["id"],
            floor_added_to_deck=item["floor_added_to_deck"],
            current_upgrade_level=item.get("current_upgrade_level"),
            enchantment=Enchantment(**item["enchantment"])
            if "enchantment" in item
            else None,
        )
        cards.append(card)
    return cards


def process_relics(relics_data: list, run_player: RunPlayer) -> list[Relic]:
    """Extract and validate relics from a player's relics list."""
    relics = []
    for item in relics_data:
        relic = Relic(
            run_player_id=run_player.run_player_id,
            id=item["id"],
            floor_added_to_deck=item["floor_added_to_deck"],
        )
        relics.append(relic)
    return relics


def process_map_points(
    run_id: str, map_point_history: list[list[dict]]
) -> list[MapPoint]:
    """Flatten the nested act arrays into a single indexed list of map points.
    Stores the raw JSON for each point alongside queryable fields."""
    map_points = []
    index = 0
    for act in map_point_history:
        for point in act:
            map_points.append(
                MapPoint(
                    run_id=run_id,
                    map_point_index=index,
                    map_point_type=point["map_point_type"],
                    raw=point,
                )
            )
            index += 1
    return map_points


def process_run(raw: dict) -> ProcessedRun:
    """Process a single raw run dict into all DB-ready records."""
    run_id = raw["run_id"]
    data = raw["data"]

    run_data = RunData(**data, run_id=run_id)

    players = []
    cards = []
    relics = []
    for player_data in data["players"]:
        player = RunPlayer(
            run_id=run_id,
            player_id=player_data["id"],
            character=player_data["character"],
            max_potion_slot_count=player_data["max_potion_slot_count"],
        )
        players.append(player)
        cards.extend(process_cards(player_data["deck"], player))
        relics.extend(process_relics(player_data["relics"], player))

    map_points = process_map_points(run_id, data["map_point_history"])

    return ProcessedRun(
        run_data=run_data,
        players=players,
        cards=cards,
        relics=relics,
        map_points=map_points,
    )
