"""Shared pytest configuration."""

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Run AnyIO tests on asyncio unless a test opts into another backend."""
    return "asyncio"

