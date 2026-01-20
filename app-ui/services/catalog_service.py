"""Catalog service for loading peripheral definitions."""
from typing import Any
from core.config import settings
from store.files import FileStore


class CatalogService:
    """Service for loading and managing peripheral catalog."""
    
    def __init__(self):
        """Initialize catalog service."""
        self.store = FileStore(str(settings.STORE_DIR))
        self._catalog: dict[str, Any] | None = None
    
    def get_catalog(self) -> dict[str, Any]:
        """
        Get peripheral catalog.
        
        Returns:
            Catalog dictionary with all peripheral definitions
        """
        if self._catalog is None:
            catalog_data = self.store.read_json(settings.CATALOG_FILE)
            if catalog_data is None:
                raise FileNotFoundError(
                    f"Catalog file not found: {settings.STORE_DIR / settings.CATALOG_FILE}"
                )
            self._catalog = catalog_data
        
        return self._catalog
    
    def reload_catalog(self) -> dict[str, Any]:
        """Force reload catalog from disk."""
        self._catalog = None
        return self.get_catalog()
