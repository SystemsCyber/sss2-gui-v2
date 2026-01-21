"""Orchestrator for coordinating services and background tasks."""
import asyncio
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
        self._was_connected = False  # Track previous connection state
    
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
        
        # If connection just established, sync state to hardware
        if connected and not self._was_connected:
            logger.info("Connection established - syncing state to hardware")
            asyncio.create_task(self.sync_state_to_hardware())
        
        self._was_connected = connected
        
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
    
    async def set_pot(self, port: int, value: int, voltage: float = None) -> None:
        """
        Set potentiometer wiper position.
        
        Args:
            port: Potentiometer port (1-16)
            value: Wiper position (0-255)
            voltage: Voltage value (0-5V). If None, calculated from value.
        """
        if not self.state_service or not self.serial_service:
            raise RuntimeError("Orchestrator not initialized")
        
        state = self.state_service.get_state()
        pot_id = f"po{port}"
        
        if pot_id not in state.get("potentiometers", {}):
            raise ValueError(f"Potentiometer {pot_id} not found in state")
        
        # Calculate voltage if not provided (use power group setting if available)
        if voltage is None:
            # Determine which group this pot belongs to and get power setting
            group_id = ((port - 1) // 2) + 1  # port 1-2 -> group 1, port 3-4 -> group 2, etc.
            group_key = f"group_{group_id}"
            power_groups = state.get("potentiometer_power_groups", {})
            power_group = power_groups.get(group_key, {})
            voltage_setting = power_group.get("voltage_setting", "5V")
            max_voltage = 12.0 if voltage_setting == "12V" else 5.0
            voltage = (value / 255.0) * max_voltage
        
        state["potentiometers"][pot_id]["wiper_position"] = value
        state["potentiometers"][pot_id]["voltage"] = voltage
        self.state_service.save_state(state)
        
        # Send serial command in background (fire-and-forget) to avoid blocking on timeouts
        asyncio.create_task(self._send_pot_command_async(port, value, voltage))
        logger.info(f"Potentiometer {port} set to {value} ({voltage:.2f}V) - command queued")
    
    async def _send_pot_command_async(self, port: int, value: int, voltage: float) -> None:
        """Send potentiometer command asynchronously without blocking."""
        try:
            # Use fire-and-forget mode - hardware may not send responses for potentiometer commands
            await self.serial_service.set_pot(port, value, wait_for_response=False)
            logger.info(f"Potentiometer {port} command sent: {value} ({voltage:.2f}V)")
        except Exception as e:
            # Log error but don't raise - state is already saved
            logger.warning(f"Potentiometer {port} command failed (state saved): {e}")
    
    async def set_pot_power(self, group_id: int, voltage_setting: str) -> None:
        """
        Set potentiometer power group voltage setting.
        
        Args:
            group_id: Power group number (1-8, where 1=pot1-2, 2=pot3-4, etc.)
            voltage_setting: '5V' or '12V'
        """
        if not self.state_service or not self.serial_service:
            raise RuntimeError("Orchestrator not initialized")
        
        # Map group_id to command number: 1->25, 2->26, 3->27, 4->28, 5->29, 6->30, 7->31, 8->32
        command_number = 24 + group_id
        voltage_value = 0 if voltage_setting == '5V' else 1
        
        state = self.state_service.get_state()
        
        # Update power group state
        if "potentiometer_power_groups" not in state:
            state["potentiometer_power_groups"] = {}
        
        group_key = f"group_{group_id}"
        if group_key not in state["potentiometer_power_groups"]:
            state["potentiometer_power_groups"][group_key] = {
                "group_id": group_key,
                "voltage_setting": voltage_setting,
                "potentiometers": []
            }
        
        state["potentiometer_power_groups"][group_key]["voltage_setting"] = voltage_setting
        self.state_service.save_state(state)
        
        # Send command in background
        asyncio.create_task(self._send_pot_power_command_async(command_number, voltage_value, group_id, voltage_setting))
        logger.info(f"Potentiometer power group {group_id} set to {voltage_setting} - command queued")
    
    async def _send_pot_power_command_async(self, command_number: int, voltage_value: int, group_id: int, voltage_setting: str) -> None:
        """Send potentiometer power command asynchronously without blocking."""
        try:
            await self.serial_service.set_pot_power(command_number, voltage_value, wait_for_response=False)
            logger.info(f"Potentiometer power group {group_id} command sent: {voltage_setting}")
        except Exception as e:
            logger.warning(f"Potentiometer power group {group_id} command failed (state saved): {e}")
    
    async def set_pot_enabled(self, port: int, enabled: bool) -> None:
        """
        Set potentiometer enabled/disabled state.
        
        Args:
            port: Potentiometer port (1-16)
            enabled: True to enable (on), False to disable (off)
        """
        if not self.state_service or not self.serial_service:
            raise RuntimeError("Orchestrator not initialized")
        
        state = self.state_service.get_state()
        pot_id = f"po{port}"
        
        if pot_id not in state.get("potentiometers", {}):
            raise ValueError(f"Potentiometer {pot_id} not found in state")
        
        # Initialize enabled field if it doesn't exist
        if "enabled" not in state["potentiometers"][pot_id]:
            state["potentiometers"][pot_id]["enabled"] = False
        
        state["potentiometers"][pot_id]["enabled"] = enabled
        self.state_service.save_state(state)
        
        # Send command in background
        asyncio.create_task(self._send_pot_enabled_command_async(port, enabled))
        logger.info(f"Potentiometer {port} {'enabled' if enabled else 'disabled'} - command queued")
    
    async def _send_pot_enabled_command_async(self, port: int, enabled: bool) -> None:
        """Send potentiometer enable/disable command asynchronously without blocking."""
        try:
            await self.serial_service.set_pot_enabled(port, enabled, wait_for_response=False)
            logger.info(f"Potentiometer {port} enable command sent: {'on' if enabled else 'off'}")
        except Exception as e:
            logger.warning(f"Potentiometer {port} enable command failed (state saved): {e}")
    
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
        
        # Handle potentiometer power group changes
        if "potentiometer_power_groups" in changes:
            for group_key, group_data in changes["potentiometer_power_groups"].items():
                if "voltage_setting" in group_data:
                    # Extract group_id from group_key (e.g., "group_1" -> 1)
                    group_id = int(group_key.replace("group_", ""))
                    voltage_setting = group_data["voltage_setting"]
                    await self.set_pot_power(group_id, voltage_setting)
        
        # Handle potentiometer changes
        if "potentiometers" in changes:
            for pot_id, pot_data in changes["potentiometers"].items():
                # Handle enabled state changes
                if "enabled" in pot_data:
                    port = int(pot_id.replace("po", ""))
                    enabled = pot_data["enabled"]
                    await self.set_pot_enabled(port, enabled)
                
                # Handle wiper position changes
                if "wiper_position" in pot_data:
                    # Extract port number from pot_id (e.g., "po1" -> 1)
                    port = int(pot_id.replace("po", ""))
                    value = pot_data["wiper_position"]
                    voltage = pot_data.get("voltage")  # Use provided voltage or calculate in set_pot
                    await self.set_pot(port, value, voltage)
    
    async def sync_state_to_hardware(self) -> None:
        """
        Synchronize backend state to hardware.
        
        This method loads the current state from storage (source of truth) and
        applies all potentiometer settings to the hardware:
        - Power group voltage settings (groups 1-8)
        - Potentiometer enabled/disabled states (ports 1-16)
        - Potentiometer wiper positions (ports 1-16)
        
        This is called automatically when the hardware connects to ensure
        the hardware matches the saved backend state.
        """
        if not self.state_service or not self.serial_service:
            logger.warning("Cannot sync state: orchestrator not initialized")
            return
        
        if not self.is_connected():
            logger.warning("Cannot sync state: hardware not connected")
            return
        
        try:
            logger.info("Starting state synchronization to hardware...")
            state = self.state_service.get_state()
            
            # Apply potentiometer power group settings
            power_groups = state.get("potentiometer_power_groups", {})
            if power_groups:
                logger.info(f"Syncing {len(power_groups)} power group(s)...")
                for group_key, group_data in power_groups.items():
                    if "voltage_setting" in group_data:
                        # Extract group_id from group_key (e.g., "group_1" -> 1)
                        try:
                            group_id = int(group_key.replace("group_", ""))
                            voltage_setting = group_data["voltage_setting"]
                            # Use existing set_pot_power method which handles state and commands
                            await self.set_pot_power(group_id, voltage_setting)
                            logger.debug(f"Synced power group {group_id} to {voltage_setting}")
                        except (ValueError, KeyError) as e:
                            logger.warning(f"Failed to sync power group {group_key}: {e}")
            
            # Apply potentiometer settings
            potentiometers = state.get("potentiometers", {})
            if potentiometers:
                logger.info(f"Syncing {len(potentiometers)} potentiometer(s)...")
                for pot_id, pot_data in potentiometers.items():
                    try:
                        # Extract port number from pot_id (e.g., "po1" -> 1)
                        port = int(pot_id.replace("po", ""))
                        
                        # Apply enabled state if present
                        if "enabled" in pot_data:
                            enabled = pot_data["enabled"]
                            await self.set_pot_enabled(port, enabled)
                            logger.debug(f"Synced potentiometer {port} enabled state: {enabled}")
                        
                        # Apply wiper position if present
                        if "wiper_position" in pot_data:
                            value = pot_data["wiper_position"]
                            voltage = pot_data.get("voltage")  # Use provided voltage or calculate in set_pot
                            await self.set_pot(port, value, voltage)
                            logger.debug(f"Synced potentiometer {port} wiper position: {value}")
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Failed to sync potentiometer {pot_id}: {e}")
            
            # Optionally apply ignition state
            if "ignition" in state:
                ignition = state["ignition"]
                try:
                    if ignition:
                        await self.engine_start()
                        logger.debug("Synced ignition: ON")
                    else:
                        await self.engine_stop()
                        logger.debug("Synced ignition: OFF")
                except Exception as e:
                    logger.warning(f"Failed to sync ignition state: {e}")
            
            logger.info("State synchronization to hardware completed")
        except Exception as e:
            logger.error(f"Error during state synchronization: {e}", exc_info=True)
    
    def is_connected(self) -> bool:
        """Check if serial port is connected."""
        if not self.serial_service:
            return False
        return self.serial_service.is_connected()
