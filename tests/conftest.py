"""Shared pytest fixtures."""

import pytest


@pytest.fixture
def suppress_warnings() -> None:
    """Silence all Python warnings for tests that intentionally read defective data."""
    import warnings

    warnings.simplefilter("ignore")
