"""Tests for cfb.io (CfbIO)."""

import warnings
from pathlib import Path

import pytest

from cfb import CfbIO

_SIMPLE_DOC = "tests/data/simple.doc"


@pytest.fixture(autouse=True)
def suppress_warnings() -> None:
    warnings.simplefilter("ignore")


def test_open_with_str_path() -> None:
    io = CfbIO(_SIMPLE_DOC)
    assert io.root.name == "Root Entry"


def test_open_with_pathlib_path() -> None:
    io = CfbIO(Path(_SIMPLE_DOC))
    assert io.root.name == "Root Entry"


def test_context_manager() -> None:
    with CfbIO(_SIMPLE_DOC) as doc:
        assert doc.root.name == "Root Entry"
        assert not doc.closed
    assert doc.closed


def test_repr() -> None:
    io = CfbIO(_SIMPLE_DOC)
    assert repr(io) == f'<CfbIO "{_SIMPLE_DOC}">'


def test_len() -> None:
    io = CfbIO(_SIMPLE_DOC)
    assert len(io) == 7


def test_getitem_by_name() -> None:
    io = CfbIO(_SIMPLE_DOC)
    entry = io["1Table"]
    assert entry.name == "1Table"


def test_getitem_by_id() -> None:
    io = CfbIO(_SIMPLE_DOC)
    entry = io[0]
    assert entry is io.root
