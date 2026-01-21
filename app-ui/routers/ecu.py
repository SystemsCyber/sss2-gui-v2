"""ECU configuration management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Optional

from services.ecu_service import ECUService


router = APIRouter(prefix="/ecu", tags=["ecu"])


class PinConfiguration(BaseModel):
    """Pin configuration for a single pin."""
    wire_color: str = ""
    ecu_function: str = ""


class ECUCreate(BaseModel):
    """ECU creation request."""
    name: str
    model: str = ""
    serial_number: str = ""
    pictures: list[str] = []  # URLs or file paths
    pins: dict[str, PinConfiguration] = {}  # Key: "J24:1", Value: PinConfiguration


class ECUUpdate(BaseModel):
    """ECU update request."""
    name: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    pictures: Optional[list[str]] = None
    pins: Optional[dict[str, PinConfiguration]] = None


class ECUItem(BaseModel):
    """ECU list item (metadata only)."""
    id: str
    name: str
    model: str
    serial_number: str
    created_at: str
    updated_at: str


class ECUFull(BaseModel):
    """Full ECU configuration."""
    id: str
    name: str
    model: str
    serial_number: str
    pictures: list[str]
    pins: dict[str, dict[str, str]]  # Key: "J24:1", Value: {"wire_color": "...", "ecu_function": "..."}
    created_at: str
    updated_at: str


def get_ecu_service() -> ECUService:
    """Dependency to get ECU service."""
    return ECUService()


@router.get("", response_model=list[ECUItem])
async def list_ecus(
    ecu_service: ECUService = Depends(get_ecu_service)
) -> list[ECUItem]:
    """List all ECU configurations."""
    try:
        ecus = ecu_service.list_ecus()
        return [ECUItem(**ecu) for ecu in ecus]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("", response_model=ECUFull)
async def create_ecu(
    create: ECUCreate,
    ecu_service: ECUService = Depends(get_ecu_service)
) -> ECUFull:
    """Create a new ECU configuration."""
    try:
        # Convert Pydantic models to dicts
        pins_dict = {
            pin_key: {
                "wire_color": pin_config.wire_color,
                "ecu_function": pin_config.ecu_function
            }
            for pin_key, pin_config in create.pins.items()
        }
        
        ecu_data = {
            "name": create.name,
            "model": create.model,
            "serial_number": create.serial_number,
            "pictures": create.pictures,
            "pins": pins_dict
        }
        
        ecu = ecu_service.create_ecu(ecu_data)
        return ECUFull(**ecu)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{ecu_id}", response_model=ECUFull)
async def get_ecu(
    ecu_id: str,
    ecu_service: ECUService = Depends(get_ecu_service)
) -> ECUFull:
    """Get a specific ECU configuration."""
    try:
        ecu = ecu_service.get_ecu(ecu_id)
        if ecu is None:
            raise HTTPException(status_code=404, detail=f"ECU not found: {ecu_id}")
        return ECUFull(**ecu)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/{ecu_id}", response_model=ECUFull)
async def update_ecu(
    ecu_id: str,
    update: ECUUpdate,
    ecu_service: ECUService = Depends(get_ecu_service)
) -> ECUFull:
    """Update an existing ECU configuration."""
    try:
        # Convert Pydantic models to dicts if pins provided
        updates: dict[str, Any] = {}
        if update.name is not None:
            updates["name"] = update.name
        if update.model is not None:
            updates["model"] = update.model
        if update.serial_number is not None:
            updates["serial_number"] = update.serial_number
        if update.pictures is not None:
            updates["pictures"] = update.pictures
        if update.pins is not None:
            updates["pins"] = {
                pin_key: {
                    "wire_color": pin_config.wire_color,
                    "ecu_function": pin_config.ecu_function
                }
                for pin_key, pin_config in update.pins.items()
            }
        
        ecu = ecu_service.update_ecu(ecu_id, updates)
        return ECUFull(**ecu)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{ecu_id}")
async def delete_ecu(
    ecu_id: str,
    ecu_service: ECUService = Depends(get_ecu_service)
) -> dict[str, str]:
    """Delete an ECU configuration."""
    try:
        deleted = ecu_service.delete_ecu(ecu_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"ECU not found: {ecu_id}")
        return {"status": "deleted", "id": ecu_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
