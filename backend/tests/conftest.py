"""
Test configuration for TeamMemoryOS backend.

Uses the live development database via TestClient.
Each test cleans up its own records to avoid cross-test contamination.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """FastAPI TestClient wrapping the full application."""
    with TestClient(app) as c:
        yield c
