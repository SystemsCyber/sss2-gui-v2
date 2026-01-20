"""Pytest configuration and fixtures."""
import pytest
import asyncio
from main import app
from middleware.orchestrator import Orchestrator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def orchestrator():
    """Create and initialize orchestrator for testing."""
    orch = Orchestrator()
    await orch.initialize()
    yield orch
    await orch.shutdown()
