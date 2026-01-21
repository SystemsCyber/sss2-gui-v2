"""SSS2 device control endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from typing import Any

from services.state_service import StateService
from services.serial_service import SerialConnectionError, CommandTimeoutError
from middleware.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/sss2", tags=["sss2"])


class IgnitionRequest(BaseModel):
    """Ignition request model."""
    on: bool


class IgnitionResponse(BaseModel):
    """Ignition response model."""
    accepted: bool
    executed: bool
    detail: str
    confirmation: str | None
    ignition: bool


class StateUpdate(BaseModel):
    """State update model."""
    state: dict[str, Any]


def get_state_service() -> StateService:
    """Dependency to get state service."""
    return StateService()


def get_orchestrator() -> Orchestrator:
    """Dependency to get orchestrator."""
    # This will be injected from main.py
    from main import get_orchestrator_instance
    return get_orchestrator_instance()


@router.get("/state")
async def get_state(
    state_service: StateService = Depends(get_state_service)
) -> dict[str, Any]:
    """Get current device state."""
    return state_service.get_state()


@router.put("/state")
async def update_state(
    update: StateUpdate,
    state_service: StateService = Depends(get_state_service),
    orchestrator: Orchestrator = Depends(get_orchestrator)
) -> dict[str, Any]:
    """Update device state."""
    try:
        updated_state = state_service.update_state(update.state)
        # Apply changes to hardware via orchestrator
        # Run in background task to avoid blocking on timeouts
        try:
            # Create background task for hardware updates
            import asyncio
            asyncio.create_task(orchestrator.apply_state_changes(update.state))
        except Exception as e:
            # Log but don't fail the request - state is already saved
            logger.warning(f"Hardware command failed (state saved): {e}")
        return updated_state
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/ignition", response_model=IgnitionResponse)
async def set_ignition(
    request: Request,
    req: IgnitionRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """Set ignition state."""
    logger.info(f"Ignition request: on={req.on} from {request.client.host if request.client else 'unknown'}")
    
    try:
        confirmation = None
        if req.on:
            confirmation = await orchestrator.engine_start()
            detail = "SSS2 ignition relay ON (setting 50,1) executed."
        else:
            confirmation = await orchestrator.engine_stop()
            detail = "SSS2 ignition relay OFF (setting 50,0) executed."
        
        response = IgnitionResponse(
            accepted=True,
            executed=True,
            detail=detail,
            confirmation=confirmation,
            ignition=req.on
        )
        
        logger.info(f"Ignition response: {response.detail}, confirmation: {confirmation}")
        return response
        
    except SerialConnectionError as e:
        logger.error(f"Ignition request failed - not connected: {e}")
        response = IgnitionResponse(
            accepted=False,
            executed=False,
            detail=f"SSS2 not connected: {str(e)}",
            confirmation=None,
            ignition=req.on
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response.detail
        ) from e
        
    except CommandTimeoutError as e:
        logger.error(f"Ignition request failed - timeout: {e}")
        response = IgnitionResponse(
            accepted=True,
            executed=False,
            detail=f"Command sent but no response received: {str(e)}",
            confirmation=None,
            ignition=req.on
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=response.detail
        ) from e
        
    except Exception as e:
        logger.error(f"Ignition request failed: {e}", exc_info=True)
        response = IgnitionResponse(
            accepted=False,
            executed=False,
            detail=f"Internal error: {str(e)}",
            confirmation=None,
            ignition=req.on
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response.detail) from e
