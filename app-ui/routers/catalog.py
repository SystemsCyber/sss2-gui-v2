"""Catalog endpoint."""
from fastapi import APIRouter, Depends
from typing import Any

from services.catalog_service import CatalogService


router = APIRouter(prefix="/catalog", tags=["catalog"])


def get_catalog_service() -> CatalogService:
    """Dependency to get catalog service."""
    return CatalogService()


@router.get("")
async def get_catalog(
    catalog_service: CatalogService = Depends(get_catalog_service)
) -> dict[str, Any]:
    """Get peripheral catalog."""
    return catalog_service.get_catalog()
