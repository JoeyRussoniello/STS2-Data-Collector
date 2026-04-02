"""Run upload and retrieval endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.dependencies import get_run_service
from app.api.schemas import (
    CardResponse,
    MapPointResponse,
    ProcessedRunResponse,
    RelicResponse,
    RunDataResponse,
    RunListResponse,
    RunPlayerResponse,
    RunResponse,
    RunUploadRequest,
)
from app.domain.services import RunService

logger = logging.getLogger("sts2.runs")

router = APIRouter(prefix="/runs", tags=["runs"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

limiter = Limiter(key_func=get_remote_address)


def _to_processed_response(processed) -> ProcessedRunResponse:
    return ProcessedRunResponse(
        run_data=RunDataResponse(**processed.run_data.model_dump()),
        players=[
            RunPlayerResponse(**player.model_dump()) for player in processed.players
        ],
        cards=[
            CardResponse(
                run_player_id=card.run_player_id,
                id=card.id,
                floor_added_to_deck=card.floor_added_to_deck,
                current_upgrade_level=card.current_upgrade_level,
                enchantment=(
                    card.enchantment.model_dump()
                    if card.enchantment is not None
                    else None
                ),
            )
            for card in processed.cards
        ],
        relics=[RelicResponse(**relic.model_dump()) for relic in processed.relics],
        map_points=[
            MapPointResponse(**point.model_dump()) for point in processed.map_points
        ],
    )


@router.post("")
@limiter.limit("60/minute")
async def upload_run(
    request: Request,
    body: RunUploadRequest,
    svc: RunService = Depends(get_run_service),
) -> RunResponse:
    if body.file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"file_size {body.file_size} exceeds maximum of {MAX_FILE_SIZE} bytes",
        )
    record = await svc.upload_run(
        steam_id=body.steam_id,
        profile=body.profile,
        file_name=body.file_name,
        file_size=body.file_size,
        data=body.data,
    )
    logger.info(
        "Uploaded run=%s profile=%s file=%s size=%d",
        record.run_id,
        record.profile,
        record.file_name,
        record.file_size,
    )
    return RunResponse(
        run_id=record.run_id,
        steam_id_hash=record.steam_id_hash,
        profile=record.profile,
        file_name=record.file_name,
        file_size=record.file_size,
        data=record.data,
        uploaded_at=record.uploaded_at,
    )


@router.get("/{run_id}")
async def get_run(
    run_id: str,
    svc: RunService = Depends(get_run_service),
) -> RunResponse:
    record = await svc.get_run(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunResponse(
        run_id=record.run_id,
        steam_id_hash=record.steam_id_hash,
        profile=record.profile,
        file_name=record.file_name,
        file_size=record.file_size,
        data=record.data,
        uploaded_at=record.uploaded_at,
    )


@router.get("/{run_id}/processed")
async def get_processed_run(
    run_id: str,
    svc: RunService = Depends(get_run_service),
) -> ProcessedRunResponse:
    processed = await svc.get_processed_run(run_id)
    if processed is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return _to_processed_response(processed)


@router.get("/by-player/{steam_id}")
async def get_runs_by_player(
    steam_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    svc: RunService = Depends(get_run_service),
) -> RunListResponse:
    runs, total = await svc.get_runs_for_player(steam_id, limit=limit, offset=offset)
    return RunListResponse(
        runs=[
            RunResponse(
                run_id=r.run_id,
                steam_id_hash=r.steam_id_hash,
                profile=r.profile,
                file_name=r.file_name,
                file_size=r.file_size,
                data=r.data,
                uploaded_at=r.uploaded_at,
            )
            for r in runs
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
