"""Tests for state load/save roundtrip."""
import pytest
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from main import app
from core.config import settings
from services.state_service import StateService


@pytest.fixture
def temp_store():
    """Create a temporary store directory for testing."""
    temp_dir = tempfile.mkdtemp()
    original_store_dir = settings.STORE_DIR
    
    settings.STORE_DIR = Path(temp_dir)
    
    yield temp_dir
    
    shutil.rmtree(temp_dir)
    settings.STORE_DIR = original_store_dir


def test_get_state(temp_store):
    """Test getting device state."""
    client = TestClient(app)
    
    response = client.get("/api/sss2/state")
    assert response.status_code == 200
    state = response.json()
    assert isinstance(state, dict)
    assert "ignition" in state
    assert "potentiometers" in state


def test_update_state(temp_store):
    """Test updating device state."""
    client = TestClient(app)
    
    # Get current state
    get_response = client.get("/api/sss2/state")
    original_state = get_response.json()
    
    # Update state
    updates = {
        "ignition": True,
        "potentiometers": {
            "po1": {
                "wiper_position": 128,
                "term_a_connect": True,
                "term_b_connect": False,
                "wiper_connect": True,
                "application": "Test Application",
                "wire_color": "RED/BLK"
            }
        }
    }
    
    update_response = client.put("/api/sss2/state", json={"state": updates})
    assert update_response.status_code == 200
    updated_state = update_response.json()
    
    assert updated_state["ignition"] == True
    assert updated_state["potentiometers"]["po1"]["wiper_position"] == 128
    assert updated_state["potentiometers"]["po1"]["application"] == "Test Application"


def test_state_persistence(temp_store):
    """Test that state persists across service instances."""
    # Create first service instance and update state
    service1 = StateService()
    service1.update_state({
        "ignition": True,
        "potentiometers": {
            "po1": {"wiper_position": 100}
        }
    })
    
    # Create second service instance and verify state persisted
    service2 = StateService()
    state = service2.get_state()
    assert state["ignition"] == True
    assert state["potentiometers"]["po1"]["wiper_position"] == 100
