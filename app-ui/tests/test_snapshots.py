"""Tests for snapshot endpoints."""
import pytest
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from main import app
from core.config import settings


@pytest.fixture
def temp_store():
    """Create a temporary store directory for testing."""
    temp_dir = tempfile.mkdtemp()
    original_store_dir = settings.STORE_DIR
    
    # Create snapshot directory
    snapshot_dir = Path(temp_dir) / settings.SNAPSHOTS_DIR
    snapshot_dir.mkdir(parents=True)
    
    # Temporarily override store directory
    settings.STORE_DIR = Path(temp_dir)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)
    settings.STORE_DIR = original_store_dir


def test_create_snapshot(temp_store):
    """Test creating a snapshot."""
    client = TestClient(app)
    
    response = client.post("/api/snapshots", json={"label": None})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "label" in data
    assert "created_at" in data


def test_list_snapshots(temp_store):
    """Test listing snapshots."""
    client = TestClient(app)
    
    # Create a snapshot first
    create_response = client.post("/api/snapshots", json={"label": "Test Snapshot"})
    assert create_response.status_code == 200
    
    # List snapshots
    list_response = client.get("/api/snapshots")
    assert list_response.status_code == 200
    snapshots = list_response.json()
    assert isinstance(snapshots, list)
    assert len(snapshots) >= 1
    assert snapshots[0]["label"] == "Test Snapshot"


def test_revert_snapshot(temp_store):
    """Test reverting to a snapshot."""
    client = TestClient(app)
    
    # Create a snapshot
    create_response = client.post("/api/snapshots", json={"label": "Test Snapshot"})
    snapshot_id = create_response.json()["id"]
    
    # Revert to snapshot
    revert_response = client.post(f"/api/snapshots/{snapshot_id}/revert")
    assert revert_response.status_code == 200
    state = revert_response.json()
    assert isinstance(state, dict)


def test_delete_snapshot(temp_store):
    """Test deleting a snapshot."""
    client = TestClient(app)
    
    # Create a snapshot
    create_response = client.post("/api/snapshots", json={"label": "Test Snapshot"})
    snapshot_id = create_response.json()["id"]
    
    # Delete snapshot
    delete_response = client.delete(f"/api/snapshots/{snapshot_id}")
    assert delete_response.status_code == 200
    
    # Verify it's deleted
    list_response = client.get("/api/snapshots")
    snapshots = list_response.json()
    assert snapshot_id not in [s["id"] for s in snapshots]
