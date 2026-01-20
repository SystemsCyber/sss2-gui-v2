"""Async serial service for SSS2 communication."""
import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable, Dict
import serial_asyncio

from core.config import settings

logger = logging.getLogger(__name__)


class SerialConnectionError(Exception):
    """Raised when serial connection is lost or unavailable."""
    pass


class CommandTimeoutError(Exception):
    """Raised when command response times out."""
    pass


class SerialService:
    """Async serial service for SSS2 communication."""
    
    def __init__(self):
        """Initialize serial service."""
        self.port = settings.SSS2_SERIAL_PORT
        self.baudrate = settings.SSS2_BAUDRATE
        self.connected = False
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._command_queue: Optional[asyncio.Queue] = None
        self._command_response_map: Dict[str, asyncio.Future] = {}
        self._command_counter = 0
        self._read_task: Optional[asyncio.Task] = None
        self._write_task: Optional[asyncio.Task] = None
        self._connection_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._heartbeat_interval = 5.0  # seconds
        self._command_timeout = 2.0  # seconds
        self._on_connection_changed: Optional[Callable[[bool, str, Optional[str]], None]] = None
        
    def set_connection_callback(self, callback: Callable[[bool, str, Optional[str]], None]) -> None:
        """Set callback for connection status changes.
        
        Args:
            callback: Function called with (connected: bool, port: str, message: Optional[str])
        """
        self._on_connection_changed = callback
    
    async def start(self) -> None:
        """Start serial service (connect and start background tasks)."""
        if self._connection_task is None:
            self._command_queue = asyncio.Queue()
            self._connection_task = asyncio.create_task(self._connection_loop())
            logger.info(f"Serial service starting on {self.port}")
    
    async def stop(self) -> None:
        """Stop serial service (disconnect and clean up tasks)."""
        self.connected = False
        
        # Cancel all tasks
        tasks = [
            self._heartbeat_task,
            self._read_task,
            self._write_task,
            self._connection_task
        ]
        
        for task in tasks:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close serial connection
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception as e:
                logger.error(f"Error closing serial writer: {e}")
            self._writer = None
        
        self._reader = None
        self._read_task = None
        self._write_task = None
        self._connection_task = None
        self._heartbeat_task = None
        
        # Cancel all pending command futures
        for future in self._command_response_map.values():
            if not future.done():
                future.cancel()
        self._command_response_map.clear()
        
        logger.info("Serial service stopped")
    
    async def send_command(self, command: str, timeout: Optional[float] = None) -> str:
        """Send a command to SSS2 and wait for response.
        
        Args:
            command: Command string to send (e.g., "50,1")
            timeout: Optional timeout in seconds (default: self._command_timeout)
            
        Returns:
            Response string from SSS2
            
        Raises:
            SerialConnectionError: If not connected
            CommandTimeoutError: If no response received within timeout
        """
        if not self.connected:
            raise SerialConnectionError(f"Not connected to {self.port}")
        
        if timeout is None:
            timeout = self._command_timeout
        
        # Create future for response
        command_id = f"{command}_{self._command_counter}"
        self._command_counter += 1
        future = asyncio.Future()
        self._command_response_map[command_id] = future
        
        try:
            # Queue command
            if self._command_queue:
                await self._command_queue.put((command, command_id))
            else:
                raise SerialConnectionError("Command queue not initialized")
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(future, timeout=timeout)
                return response
            except asyncio.TimeoutError:
                self._command_response_map.pop(command_id, None)
                raise CommandTimeoutError(f"Command '{command}' timed out after {timeout}s")
        except Exception as e:
            self._command_response_map.pop(command_id, None)
            raise
    
    async def _connection_loop(self) -> None:
        """Background task for managing serial connection."""
        while True:
            try:
                # Check if device exists
                port_path = Path(self.port)
                if not port_path.exists():
                    logger.warning(f"Serial port {self.port} does not exist")
                    self.connected = False
                    if self._on_connection_changed:
                        self._on_connection_changed(False, self.port, "Device not found")
                    await asyncio.sleep(self._heartbeat_interval)
                    continue
                
                # Try to connect
                logger.info(f"Connecting to {self.port} at {self.baudrate} baud...")
                try:
                    self._reader, self._writer = await serial_asyncio.open_serial_connection(
                        url=self.port,
                        baudrate=self.baudrate
                    )
                    
                    self.connected = True
                    logger.info(f"Connected to {self.port}")
                    
                    if self._on_connection_changed:
                        self._on_connection_changed(True, self.port, "Connected")
                    
                    # Start read and write tasks
                    if self._read_task is None:
                        self._read_task = asyncio.create_task(self._read_loop())
                    
                    if self._write_task is None:
                        self._write_task = asyncio.create_task(self._write_loop())
                    
                    # Start heartbeat task
                    if self._heartbeat_task is None:
                        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                    
                    # Wait for connection to fail (read/write tasks will handle errors)
                    await asyncio.gather(
                        self._read_task,
                        self._write_task,
                        self._heartbeat_task,
                        return_exceptions=True
                    )
                    
                except serial_asyncio.serial.SerialException as e:
                    logger.error(f"Serial connection error: {e}")
                    self.connected = False
                    if self._on_connection_changed:
                        self._on_connection_changed(False, self.port, str(e))
                    
                    # Clean up failed connection
                    if self._writer:
                        try:
                            self._writer.close()
                            await self._writer.wait_closed()
                        except Exception:
                            pass
                        self._writer = None
                    self._reader = None
                    
                    # Cancel tasks
                    for task in [self._read_task, self._write_task, self._heartbeat_task]:
                        if task:
                            task.cancel()
                            try:
                                await task
                            except asyncio.CancelledError:
                                pass
                    
                    self._read_task = None
                    self._write_task = None
                    self._heartbeat_task = None
                    
                    await asyncio.sleep(5)  # Retry after 5 seconds
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Connection loop error: {e}", exc_info=True)
                self.connected = False
                if self._on_connection_changed:
                    self._on_connection_changed(False, self.port, str(e))
                await asyncio.sleep(5)  # Retry after 5 seconds
    
    async def _write_loop(self) -> None:
        """Background task for writing commands to serial port."""
        if self._command_queue is None or self._writer is None:
            return
        
        while self.connected:
            try:
                command, command_id = await asyncio.wait_for(
                    self._command_queue.get(),
                    timeout=1.0
                )
                
                if not self.connected or self._writer is None:
                    break
                
                # Write command with newline
                command_bytes = f"{command}\r\n".encode('ascii')
                self._writer.write(command_bytes)
                await self._writer.drain()
                
                logger.info(f"Sending command: {command}")
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Write error: {e}", exc_info=True)
                # Mark connection as failed
                self.connected = False
                if self._on_connection_changed:
                    self._on_connection_changed(False, self.port, f"Write error: {e}")
                break
    
    async def _read_loop(self) -> None:
        """Background task for reading responses from serial port."""
        if self._reader is None:
            return
        
        while self.connected:
            try:
                if self._reader is None:
                    break
                
                # Read line with timeout
                try:
                    line = await asyncio.wait_for(
                        self._reader.readline(),
                        timeout=1.0
                    )
                    
                    if not line:
                        continue
                    
                    # Decode and strip
                    response = line.decode('ascii', errors='ignore').strip()
                    
                    if not response:
                        continue
                    
                    logger.info(f"Received response: {response}")
                    
                    # Parse and match response to pending command
                    self._parse_response(response)
                    
                except asyncio.TimeoutError:
                    # Timeout is OK, continue reading
                    continue
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Read error: {e}", exc_info=True)
                # Mark connection as failed
                self.connected = False
                if self._on_connection_changed:
                    self._on_connection_changed(False, self.port, f"Read error: {e}")
                break
    
    def _parse_response(self, response: str) -> None:
        """Parse response and match to pending command.
        
        Args:
            response: Response string from SSS2
        """
        # Try to match response to pending commands
        # Strategy: Match any pending command, use first one
        # In practice, responses might be echo, "OK", "ACK", or error messages
        
        matched = False
        for command_id, future in list(self._command_response_map.items()):
            if not future.done():
                # Accept response for this command
                # For now, accept any response as confirmation
                future.set_result(response)
                self._command_response_map.pop(command_id, None)
                matched = True
                break
        
        if not matched:
            # No pending command, log as unexpected
            logger.debug(f"Unexpected response (no pending command): {response}")
    
    async def _heartbeat_loop(self) -> None:
        """Background task for monitoring connection health."""
        while self.connected:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                
                if not self.connected:
                    break
                
                # Check device presence
                port_path = Path(self.port)
                if not port_path.exists():
                    logger.warning(f"Heartbeat: Port {self.port} no longer exists")
                    self.connected = False
                    if self._on_connection_changed:
                        self._on_connection_changed(False, self.port, "Device disconnected")
                    break
                
                # Check if writer is still valid
                if self._writer is None or self._writer.is_closing():
                    logger.warning("Heartbeat: Writer is closed")
                    self.connected = False
                    if self._on_connection_changed:
                        self._on_connection_changed(False, self.port, "Connection lost")
                    break
                
                # Connection is healthy
                logger.debug(f"Heartbeat: Connection healthy on {self.port}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}", exc_info=True)
                self.connected = False
                if self._on_connection_changed:
                    self._on_connection_changed(False, self.port, f"Heartbeat error: {e}")
                break
    
    def is_connected(self) -> bool:
        """Check if serial port is connected."""
        return self.connected
    
    async def engine_start(self) -> str:
        """Send engine start command (ignition ON) and wait for confirmation.
        
        Returns:
            Confirmation response from SSS2
            
        Raises:
            SerialConnectionError: If not connected
            CommandTimeoutError: If no response received
        """
        if not self.connected:
            raise SerialConnectionError(f"Not connected to {self.port}")
        
        return await self.send_command("50,1")
    
    async def engine_stop(self) -> str:
        """Send engine stop command (ignition OFF) and wait for confirmation.
        
        Returns:
            Confirmation response from SSS2
            
        Raises:
            SerialConnectionError: If not connected
            CommandTimeoutError: If no response received
        """
        if not self.connected:
            raise SerialConnectionError(f"Not connected to {self.port}")
        
        return await self.send_command("50,0")
    
    async def set_pot(self, port: int, value: int) -> str:
        """Set potentiometer wiper position and wait for confirmation.
        
        Args:
            port: Potentiometer port (1-16)
            value: Wiper position (0-255)
            
        Returns:
            Confirmation response from SSS2
            
        Raises:
            SerialConnectionError: If not connected
            CommandTimeoutError: If no response received
        """
        if not self.connected:
            raise SerialConnectionError(f"Not connected to {self.port}")
        
        command = f"{port},{value}"
        return await self.send_command(command)
