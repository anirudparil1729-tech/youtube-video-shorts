"""Pytest configuration and shared fixtures."""

import asyncio
import pytest
from pathlib import Path
import tempfile


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create and clean up temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_youtube_url():
    """Return a mock YouTube URL for testing."""
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
