"""Snapshot management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any

from services.snapshot_service import SnapshotService
from services.state_service import StateService


router = APIRouter(prefix="/snapshots", tags=["snapshots"])


class SnapshotCreate(BaseModel):
    """Snapshot creation request."""
    label: str | None = None


class SnapshotItem(BaseModel):
    """Snapshot item response."""
    id: str
    label: str
    created_at: str


def get_snapshot_service() -> SnapshotService:
    """Dependency to get snapshot service."""
    state_service = StateService()
    return SnapshotService(state_service)


@router.post("", response_model=SnapshotItem)
async def create_snapshot(
    create: SnapshotCreate,
    snapshot_service: SnapshotService = Depends(get_snapshot_service)
) -> SnapshotItem:
    """Create a new snapshot from current state."""
    try:
        snapshot = snapshot_service.create_snapshot(create.label)
        return SnapshotItem(**snapshot)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("", response_model=list[SnapshotItem])
async def list_snapshots(
    snapshot_service: SnapshotService = Depends(get_snapshot_service)
) -> list[SnapshotItem]:
    """List all snapshots (newest first)."""
    try:
        snapshots = snapshot_service.list_snapshots()
        return [SnapshotItem(**s) for s in snapshots]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{snapshot_id}/revert")
async def revert_snapshot(
    snapshot_id: str,
    snapshot_service: SnapshotService = Depends(get_snapshot_service)
) -> dict[str, Any]:
    """Revert current state to a snapshot."""
    try:
        state = snapshot_service.revert_snapshot(snapshot_id)
        return state
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{snapshot_id}")
async def delete_snapshot(
    snapshot_id: str,
    snapshot_service: SnapshotService = Depends(get_snapshot_service)
) -> dict[str, str]:
    """Delete a snapshot."""
    try:
        deleted = snapshot_service.delete_snapshot(snapshot_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Snapshot not found: {snapshot_id}")
        return {"status": "deleted", "id": snapshot_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
