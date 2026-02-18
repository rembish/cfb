"""Shared pytest fixtures for cfb tests."""

from __future__ import annotations

import warnings
from collections.abc import Iterator

import pytest

from cfb import CfbIO

_SIMPLE_DOC = "tests/data/simple.doc"


@pytest.fixture(autouse=True)
def suppress_warnings() -> Iterator[None]:
    """Suppress all Python warnings for the duration of each test.

    Uses ``catch_warnings()`` so that the filter is properly restored
    after each test and does not bleed into subsequent tests.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield


@pytest.fixture
def doc() -> Iterator[CfbIO]:
    """Open simple.doc as a CfbIO (eager directory load) and close it after the test."""
    with CfbIO(_SIMPLE_DOC) as io:
        yield io


@pytest.fixture
def lazy_doc() -> Iterator[CfbIO]:
    """Open simple.doc lazily (no eager directory read) and close it after the test."""
    with CfbIO(_SIMPLE_DOC, lazy=True) as io:
        yield io
