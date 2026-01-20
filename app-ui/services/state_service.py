"""State service for loading and saving device state."""
from typing import Any
from datetime import datetime
from core.config import settings
from store.files import FileStore


class StateService:
    """Service for loading and saving device state."""
    
    def __init__(self):
        """Initialize state service."""
        self.store = FileStore(str(settings.STORE_DIR))
        self._state: dict[str, Any] | None = None
    
    def get_state(self) -> dict[str, Any]:
        """
        Get current device state.
        
        Returns:
            Current device state dictionary
        """
        if self._state is None:
            state_data = self.store.read_json(settings.STATE_FILE)
            if state_data is None:
                # Initialize with default state if file doesn't exist
                state_data = self._get_default_state()
                self.save_state(state_data)
            self._state = state_data
        
        return self._state
    
    def save_state(self, state: dict[str, Any] | None = None) -> None:
        """
        Save device state.
        
        Args:
            state: State dictionary to save, or None to save current cached state
        """
        if state is None:
            state = self._state
        
        if state is None:
            raise ValueError("No state to save")
        
        # Update timestamp
        state["last_updated"] = datetime.utcnow().isoformat() + "Z"
        
        self.store.write_json(settings.STATE_FILE, state)
        self._state = state
    
    def update_state(self, updates: dict[str, Any]) -> dict[str, Any]:
        """
        Update state with partial updates.
        
        Args:
            updates: Partial state updates (will be merged into current state)
            
        Returns:
            Updated state
        """
        state = self.get_state()
        
        # Deep merge updates
        self._deep_merge(state, updates)
        
        self.save_state(state)
        return state
    
    def _deep_merge(self, base: dict[str, Any], updates: dict[str, Any]) -> None:
        """Deep merge updates into base dictionary."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _get_default_state(self) -> dict[str, Any]:
        """Get default state structure."""
        # Load default from file if it exists, otherwise return minimal structure
        default_data = self.store.read_json(settings.STATE_FILE)
        if default_data:
            return default_data
        
        return {
            "sss2_version": None,
            "last_updated": None,
            "connected_port": None,
            "ignition": False,
            "potentiometers": {},
            "vouts": {},
            "pwms": {},
            "can": {},
            "j1708": {}
        }
