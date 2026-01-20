"""JSON file I/O utilities with safe read/write and atomic operations."""
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Optional
import fcntl


class FileStore:
    """Safe file-based JSON storage with atomic writes."""
    
    def __init__(self, base_path: str):
        """Initialize store with base directory path."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def read_json(self, filename: str) -> Optional[Any]:
        """
        Read JSON file, return None if file doesn't exist.
        
        Args:
            filename: Relative filename within base_path
            
        Returns:
            Parsed JSON data or None if file doesn't exist
        """
        file_path = self.base_path / filename
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Use file locking for reads on Unix systems (optional)
                try:
                    if hasattr(fcntl, 'flock'):
                        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    return json.load(f)
                finally:
                    if hasattr(fcntl, 'flock'):
                        try:
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                        except:
                            pass
        except (json.JSONDecodeError, IOError) as e:
            raise IOError(f"Failed to read {file_path}: {e}") from e
    
    def write_json(self, filename: str, data: Any) -> None:
        """
        Write JSON file atomically (write to temp, then rename).
        
        Args:
            filename: Relative filename within base_path
            data: Data to serialize as JSON
        """
        file_path = self.base_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create temp file in same directory for atomic rename
        temp_fd, temp_path = tempfile.mkstemp(
            suffix='.tmp',
            dir=file_path.parent,
            text=True
        )
        
        try:
            # Write to temp file
            with open(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            
            # Atomic rename
            os.replace(temp_path, file_path)
        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise IOError(f"Failed to write {file_path}: {e}") from e
    
    def list_files(self, pattern: str = "*") -> list[str]:
        """
        List files in base_path matching pattern.
        
        Args:
            pattern: Glob pattern (e.g., "*.json")
            
        Returns:
            List of filenames (relative to base_path)
        """
        return [f.name for f in self.base_path.glob(pattern)]
    
    def delete_file(self, filename: str) -> bool:
        """
        Delete a file.
        
        Args:
            filename: Relative filename within base_path
            
        Returns:
            True if deleted, False if didn't exist
        """
        file_path = self.base_path / filename
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except OSError:
            return False
