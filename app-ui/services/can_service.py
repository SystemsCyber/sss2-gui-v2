"""CAN bus service (stub for future implementation)."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class CANService:
    """CAN bus service - stub implementation."""
    
    def __init__(self):
        """Initialize CAN service."""
        self._listening = False
        self._detected_buses: list[dict[str, Any]] = []
    
    async def start(self) -> None:
        """Start CAN service (stub)."""
        logger.info("CAN service starting (stub)")
        # TODO: Initialize python-can interface
        # self._detected_buses = await self.detect_buses()
    
    async def stop(self) -> None:
        """Stop CAN service."""
        self._listening = False
        logger.info("CAN service stopped")
    
    async def detect_buses(self) -> list[dict[str, Any]]:
        """
        Detect available CAN buses (stub).
        
        Returns:
            List of detected CAN bus information dictionaries
        """
        # Stub: Return empty list
        # TODO: Implement real CAN bus detection using python-can
        logger.info("Detecting CAN buses (stub)")
        return []
    
    async def start_listening(self, bus_id: str, bitrate: int = 500000) -> None:
        """
        Start listening on a CAN bus (stub).
        
        Args:
            bus_id: CAN bus identifier
            bitrate: CAN bus bitrate (default 500000)
        """
        logger.info(f"Starting CAN listener on bus {bus_id} at {bitrate} bps (stub)")
        self._listening = True
        # TODO: Implement real CAN listening using python-can
    
    def is_listening(self) -> bool:
        """Check if CAN service is listening."""
        return self._listening
