"""Run upload and retrieval endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_run_service
from app.api.schemas import RunListResponse, RunResponse, RunUploadRequest
from app.domain.services import RunService

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("/")
async def upload_run(
    body: RunUploadRequest,
    svc: RunService = Depends(get_run_service),
) -> RunResponse:
    record = await svc.upload_run(
        steam_id=body.steam_id,
        profile=body.profile,
        file_name=body.file_name,
        file_size=body.file_size,
        data=body.data,
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
