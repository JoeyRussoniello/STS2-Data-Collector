"""Public read-only API — no authentication required."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.dependencies import get_run_service
from app.api.schemas import RunListResponse, RunResponse
from app.domain.services import RunService

router = APIRouter(prefix="/api/runs", tags=["public"])

limiter = Limiter(key_func=get_remote_address)


@router.get("")
@limiter.limit("30/minute")
async def list_runs(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    svc: RunService = Depends(get_run_service),
) -> RunListResponse:
    """List all runs, newest first."""
    runs, total = await svc.list_runs(limit=limit, offset=offset)
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


@router.get("/{run_id:path}")
@limiter.limit("30/minute")
async def get_run(
    request: Request,
    run_id: str,
    svc: RunService = Depends(get_run_service),
) -> RunResponse:
    """Get a single run by ID."""
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
