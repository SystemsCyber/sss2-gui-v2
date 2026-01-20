"""Tests for health endpoint."""
import pytest
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_health_check():
    """Test health endpoint returns ok."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "connected" in data
    assert isinstance(data["connected"], bool)
