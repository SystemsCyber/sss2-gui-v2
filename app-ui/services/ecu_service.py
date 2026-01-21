"""ECU configuration management service."""
import json
from typing import Any, Optional
from datetime import datetime
from pathlib import Path

from core.config import settings
from store.files import FileStore


class ECUService:
    """Service for managing ECU configurations."""
    
    def __init__(self):
        """Initialize ECU service."""
        self.store = FileStore(str(settings.STORE_DIR / "ecus"))
        # Ensure directory exists
        (settings.STORE_DIR / "ecus").mkdir(parents=True, exist_ok=True)
    
    def _get_ecu_filename(self, ecu_id: str) -> str:
        """Get filename for ECU configuration."""
        return f"{ecu_id}.json"
    
    def _sanitize_id(self, name: str) -> str:
        """Convert name to a valid filename-safe ID."""
        # Replace spaces and special chars with underscores, lowercase
        return "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in name.lower()).strip('_')
    
    def list_ecus(self) -> list[dict[str, Any]]:
        """
        List all ECU configurations.
        
        Returns:
            List of ECU metadata (id, name, model, serial_number, created_at, updated_at)
        """
        ecu_files = self.store.list_files("*.json")
        ecus = []
        
        for filename in ecu_files:
            ecu_id = filename.replace(".json", "")
            ecu_data = self.store.read_json(filename)
            if ecu_data:
                ecus.append({
                    "id": ecu_id,
                    "name": ecu_data.get("name", ecu_id),
                    "model": ecu_data.get("model", ""),
                    "serial_number": ecu_data.get("serial_number", ""),
                    "created_at": ecu_data.get("created_at", ""),
                    "updated_at": ecu_data.get("updated_at", "")
                })
        
        # Sort by updated_at (newest first)
        ecus.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return ecus
    
    def get_ecu(self, ecu_id: str) -> Optional[dict[str, Any]]:
        """
        Get ECU configuration by ID.
        
        Args:
            ecu_id: ECU identifier
            
        Returns:
            ECU configuration dictionary or None if not found
        """
        filename = self._get_ecu_filename(ecu_id)
        return self.store.read_json(filename)
    
    def create_ecu(self, ecu_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new ECU configuration.
        
        Args:
            ecu_data: ECU configuration data (name, model, serial_number, pins, pictures)
            
        Returns:
            Created ECU configuration with generated ID
        """
        name = ecu_data.get("name", "Unnamed ECU")
        ecu_id = ecu_data.get("id")
        
        if not ecu_id:
            # Generate ID from name
            base_id = self._sanitize_id(name)
            ecu_id = base_id
            counter = 1
            # Ensure unique ID
            while self.get_ecu(ecu_id) is not None:
                ecu_id = f"{base_id}_{counter}"
                counter += 1
        
        # Check if ECU with this ID already exists
        if self.get_ecu(ecu_id) is not None:
            raise ValueError(f"ECU with ID '{ecu_id}' already exists")
        
        now = datetime.utcnow().isoformat() + "Z"
        
        ecu_config = {
            "id": ecu_id,
            "name": name,
            "model": ecu_data.get("model", ""),
            "serial_number": ecu_data.get("serial_number", ""),
            "pictures": ecu_data.get("pictures", []),
            "pins": ecu_data.get("pins", {}),
            "created_at": now,
            "updated_at": now
        }
        
        filename = self._get_ecu_filename(ecu_id)
        self.store.write_json(filename, ecu_config)
        
        return ecu_config
    
    def update_ecu(self, ecu_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        """
        Update an existing ECU configuration.
        
        Args:
            ecu_id: ECU identifier
            updates: Partial updates to apply
            
        Returns:
            Updated ECU configuration
            
        Raises:
            FileNotFoundError: If ECU doesn't exist
        """
        ecu = self.get_ecu(ecu_id)
        if ecu is None:
            raise FileNotFoundError(f"ECU not found: {ecu_id}")
        
        # Update fields
        if "name" in updates:
            ecu["name"] = updates["name"]
        if "model" in updates:
            ecu["model"] = updates["model"]
        if "serial_number" in updates:
            ecu["serial_number"] = updates["serial_number"]
        if "pictures" in updates:
            ecu["pictures"] = updates["pictures"]
        if "pins" in updates:
            ecu["pins"] = updates["pins"]
        
        ecu["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        filename = self._get_ecu_filename(ecu_id)
        self.store.write_json(filename, ecu)
        
        return ecu
    
    def delete_ecu(self, ecu_id: str) -> bool:
        """
        Delete an ECU configuration.
        
        Args:
            ecu_id: ECU identifier
            
        Returns:
            True if deleted, False if not found
        """
        filename = self._get_ecu_filename(ecu_id)
        return self.store.delete_file(filename)
