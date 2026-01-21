"""Connection status WebSocket endpoint."""
import asyncio
import json
import logging
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel

from middleware.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connection", tags=["connection"])


class ConnectionStatusResponse(BaseModel):
    connected: bool
    port: str
    message: str | None


def get_orchestrator() -> Orchestrator:
    """Dependency to get orchestrator."""
    from main import get_orchestrator_instance
    return get_orchestrator_instance()


# Set of active WebSocket connections
_active_connections: Set[WebSocket] = set()


@router.get("/status", response_model=ConnectionStatusResponse)
async def get_connection_status(orchestrator: Orchestrator = Depends(get_orchestrator)):
    """Get current connection status via REST API."""
    is_connected = orchestrator.is_connected()
    port = orchestrator.serial_service.port if orchestrator.serial_service else "unknown"
    message = "Connected" if is_connected else "Disconnected"
    
    logger.info(f"REST API connection status check: connected={is_connected}, port={port}")
    
    return ConnectionStatusResponse(
        connected=is_connected,
        port=port,
        message=message
    )


def broadcast_connection_status(connected: bool, port: str, message: str | None) -> None:
    """Broadcast connection status to all connected WebSocket clients.
    
    Args:
        connected: Whether device is connected
        port: Serial port name
        message: Optional status message
    """
    payload = {
        "type": "connection_status",
        "connected": connected,
        "port": port,
        "message": message
    }
    
    # Remove disconnected clients
    disconnected = set()
    for connection in _active_connections.copy():
        try:
            asyncio.create_task(connection.send_json(payload))
        except Exception as e:
            logger.debug(f"Failed to send to WebSocket client: {e}")
            disconnected.add(connection)
    
    # Clean up disconnected clients
    for connection in disconnected:
        _active_connections.discard(connection)
    
    if _active_connections:
        logger.debug(f"Broadcasted connection status to {len(_active_connections)} clients")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for connection status updates."""
    await websocket.accept()
    _active_connections.add(websocket)
    logger.info(f"WebSocket client connected. Total clients: {len(_active_connections)}")
    
    orchestrator = get_orchestrator()
    on_connection_changed = None
    
    try:
        # Register callback for connection status changes FIRST
        # This ensures we don't miss connection status updates that happen
        # between WebSocket connection and callback registration
        def on_connection_changed(connected: bool, port: str, message: str | None) -> None:
            """Callback for connection status changes."""
            try:
                asyncio.create_task(websocket.send_json({
                    "type": "connection_status",
                    "connected": connected,
                    "port": port,
                    "message": message
                }))
            except Exception as e:
                logger.debug(f"Failed to send connection status update: {e}")
        
        orchestrator.register_connection_callback(on_connection_changed)
        
        # Send initial connection status
        is_connected = orchestrator.is_connected()
        port = orchestrator.serial_service.port if orchestrator.serial_service else "unknown"
        
        await websocket.send_json({
            "type": "connection_status",
            "connected": is_connected,
            "port": port,
            "message": "Connected" if is_connected else "Disconnected"
        })
        
        # Re-check connection status after a short delay to catch any
        # connection that might have happened during WebSocket setup
        await asyncio.sleep(0.5)
        current_connected = orchestrator.is_connected()
        current_port = orchestrator.serial_service.port if orchestrator.serial_service else "unknown"
        
        # Only send update if status changed
        if current_connected != is_connected or current_port != port:
            await websocket.send_json({
                "type": "connection_status",
                "connected": current_connected,
                "port": current_port,
                "message": "Connected" if current_connected else "Disconnected"
            })
        
        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for client ping or timeout
                await websocket.receive_text()
                # Echo back or handle ping/pong
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        _active_connections.discard(websocket)
        if on_connection_changed:
            try:
                orchestrator.unregister_connection_callback(on_connection_changed)
            except Exception:
                pass
        logger.info(f"WebSocket client disconnected. Total clients: {len(_active_connections)}")
