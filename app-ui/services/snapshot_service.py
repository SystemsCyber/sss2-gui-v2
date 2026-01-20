"""Snapshot service for managing device state snapshots."""
import os
from datetime import datetime
from typing import Any
from pathlib import Path

from core.config import settings
from store.files import FileStore
from services.state_service import StateService


class SnapshotService:
    """Service for creating, listing, and reverting snapshots."""
    
    def __init__(self, state_service: StateService):
        """
        Initialize snapshot service.
        
        Args:
            state_service: State service instance
        """
        self.state_service = state_service
        self.store = FileStore(str(settings.STORE_DIR / settings.SNAPSHOTS_DIR))
    
    def create_snapshot(self, label: str | None = None) -> dict[str, Any]:
        """
        Create a snapshot from current state.
        
        Args:
            label: Optional human-readable label (defaults to timestamp)
            
        Returns:
            Snapshot metadata dictionary
        """
        current_state = self.state_service.get_state()
        snapshot_id = self._generate_snapshot_id()
        
        if label is None:
            label = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        snapshot_data = {
            "snapshot_id": snapshot_id,
            "label": label,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "state": current_state.copy()
        }
        
        filename = f"{snapshot_id}.json"
        self.store.write_json(filename, snapshot_data)
        
        return {
            "id": snapshot_id,
            "label": label,
            "created_at": snapshot_data["created_at"]
        }
    
    def list_snapshots(self) -> list[dict[str, Any]]:
        """
        List all snapshots, sorted by creation time (newest first).
        
        Returns:
            List of snapshot metadata dictionaries
        """
        snapshot_files = self.store.list_files("*.json")
        snapshots = []
        
        for filename in snapshot_files:
            try:
                snapshot_data = self.store.read_json(filename)
                if snapshot_data:
                    snapshots.append({
                        "id": snapshot_data.get("snapshot_id", filename.replace(".json", "")),
                        "label": snapshot_data.get("label", "Unknown"),
                        "created_at": snapshot_data.get("created_at", "")
                    })
            except Exception:
                # Skip invalid snapshot files
                continue
        
        # Sort by created_at descending (newest first)
        snapshots.sort(
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        
        return snapshots
    
    def get_snapshot(self, snapshot_id: str) -> dict[str, Any] | None:
        """
        Get a specific snapshot by ID.
        
        Args:
            snapshot_id: Snapshot ID
            
        Returns:
            Snapshot data or None if not found
        """
        filename = f"{snapshot_id}.json"
        return self.store.read_json(filename)
    
    def revert_snapshot(self, snapshot_id: str) -> dict[str, Any]:
        """
        Revert current state to a snapshot.
        
        Args:
            snapshot_id: Snapshot ID to revert to
            
        Returns:
            Updated state dictionary
            
        Raises:
            FileNotFoundError: If snapshot doesn't exist
        """
        snapshot_data = self.get_snapshot(snapshot_id)
        if snapshot_data is None:
            raise FileNotFoundError(f"Snapshot not found: {snapshot_id}")
        
        state = snapshot_data.get("state")
        if state is None:
            raise ValueError(f"Snapshot {snapshot_id} has no state data")
        
        # Update current state with snapshot state
        self.state_service.save_state(state)
        
        # TODO: Trigger orchestrator to apply state changes to hardware
        
        return state
    
    def delete_snapshot(self, snapshot_id: str) -> bool:
        """
        Delete a snapshot.
        
        Args:
            snapshot_id: Snapshot ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        filename = f"{snapshot_id}.json"
        return self.store.delete_file(filename)
    
    def _generate_snapshot_id(self) -> str:
        """Generate a unique snapshot ID based on timestamp."""
        return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
