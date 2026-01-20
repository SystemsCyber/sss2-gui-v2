"""Orchestrator for coordinating services and background tasks."""
import logging
from typing import Optional, Callable, Set

from services.serial_service import SerialService
from services.can_service import CANService
from services.state_service import StateService
from services.snapshot_service import SnapshotService

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Orchestrator that coordinates services and manages background tasks.
    
    This is the central coordination point for the application:
    - Manages service lifecycle
    - Routes commands from API to services
    - Schedules background tasks
    - Manages connection status callbacks
    """
    
    def __init__(self):
        """Initialize orchestrator."""
        self.serial_service: Optional[SerialService] = None
        self.can_service: Optional[CANService] = None
        self.state_service: Optional[StateService] = None
        self.snapshot_service: Optional[SnapshotService] = None
        self._initialized = False
        self._connection_callbacks: Set[Callable[[bool, str, Optional[str]], None]] = set()
    
    def register_connection_callback(self, callback: Callable[[bool, str, Optional[str]], None]) -> None:
        """Register a callback for connection status changes.
        
        Args:
            callback: Function called with (connected: bool, port: str, message: Optional[str])
        """
        self._connection_callbacks.add(callback)
        logger.debug(f"Registered connection callback: {callback}")
    
    def unregister_connection_callback(self, callback: Callable[[bool, str, Optional[str]], None]) -> None:
        """Unregister a connection status callback.
        
        Args:
            callback: Callback function to remove
        """
        self._connection_callbacks.discard(callback)
        logger.debug(f"Unregistered connection callback: {callback}")
    
    def _on_connection_changed(self, connected: bool, port: str, message: Optional[str]) -> None:
        """Handle connection status change and notify all callbacks.
        
        Args:
            connected: Whether device is connected
            port: Serial port name
            message: Optional status message
        """
        logger.info(f"Connection status changed: connected={connected}, port={port}, message={message}")
        for callback in self._connection_callbacks.copy():
            try:
                callback(connected, port, message)
            except Exception as e:
                logger.error(f"Error in connection callback: {e}", exc_info=True)
    
    async def initialize(self) -> None:
        """Initialize orchestrator and start all services."""
        if self._initialized:
            return
        
        logger.info("Initializing orchestrator...")
        
        # Initialize services
        self.state_service = StateService()
        self.snapshot_service = SnapshotService(self.state_service)
        self.serial_service = SerialService()
        self.can_service = CANService()
        
        # Register connection status callback
        self.serial_service.set_connection_callback(self._on_connection_changed)
        
        # Start background services
        await self.serial_service.start()
        await self.can_service.start()
        
        self._initialized = True
        logger.info("Orchestrator initialized")
    
    async def shutdown(self) -> None:
        """Shutdown orchestrator and stop all services."""
        if not self._initialized:
            return
        
        logger.info("Shutting down orchestrator...")
        
        if self.serial_service:
            await self.serial_service.stop()
        
        if self.can_service:
            await self.can_service.stop()
        
        self._initialized = False
        logger.info("Orchestrator shut down")
    
    async def engine_start(self) -> str:
        """
        Start engine (ignition ON).
        
        Updates state and sends command to serial service.
        
        Returns:
            Confirmation response from SSS2
            
        Raises:
            RuntimeError: If orchestrator not initialized
            SerialConnectionError: If not connected
            CommandTimeoutError: If no response received
        """
        if not self.state_service or not self.serial_service:
            raise RuntimeError("Orchestrator not initialized")
        
        state = self.state_service.get_state()
        state["ignition"] = True
        self.state_service.save_state(state)
        
        response = await self.serial_service.engine_start()
        logger.info(f"Engine start command confirmed: {response}")
        return response
    
    async def engine_stop(self) -> str:
        """
        Stop engine (ignition OFF).
        
        Updates state and sends command to serial service.
        
        Returns:
            Confirmation response from SSS2
            
        Raises:
            RuntimeError: If orchestrator not initialized
            SerialConnectionError: If not connected
            CommandTimeoutError: If no response received
        """
        if not self.state_service or not self.serial_service:
            raise RuntimeError("Orchestrator not initialized")
        
        state = self.state_service.get_state()
        state["ignition"] = False
        self.state_service.save_state(state)
        
        response = await self.serial_service.engine_stop()
        logger.info(f"Engine stop command confirmed: {response}")
        return response
    
    async def set_pot(self, port: int, value: int) -> None:
        """
        Set potentiometer wiper position.
        
        Args:
            port: Potentiometer port (1-16)
            value: Wiper position (0-255)
        """
        if not self.state_service or not self.serial_service:
            raise RuntimeError("Orchestrator not initialized")
        
        state = self.state_service.get_state()
        pot_id = f"po{port}"
        
        if pot_id not in state.get("potentiometers", {}):
            raise ValueError(f"Potentiometer {pot_id} not found in state")
        
        state["potentiometers"][pot_id]["wiper_position"] = value
        self.state_service.save_state(state)
        
        await self.serial_service.set_pot(port, value)
        logger.info(f"Potentiometer {port} set to {value}")
    
    async def apply_state_changes(self, changes: dict) -> None:
        """
        Apply state changes to hardware.
        
        Args:
            changes: Dictionary of state changes
        """
        if not self.state_service or not self.serial_service:
            raise RuntimeError("Orchestrator not initialized")
        
        # Handle ignition changes
        if "ignition" in changes:
            if changes["ignition"]:
                await self.engine_start()
            else:
                await self.engine_stop()
        
        # Handle potentiometer changes
        if "potentiometers" in changes:
            for pot_id, pot_data in changes["potentiometers"].items():
                if "wiper_position" in pot_data:
                    # Extract port number from pot_id (e.g., "po1" -> 1)
                    port = int(pot_id.replace("po", ""))
                    value = pot_data["wiper_position"]
                    await self.set_pot(port, value)
    
    def is_connected(self) -> bool:
        """Check if serial port is connected."""
        if not self.serial_service:
            return False
        return self.serial_service.is_connected()
