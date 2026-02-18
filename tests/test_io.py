"""Tests for cfb.io (CfbIO)."""

from pathlib import Path

from cfb import CfbIO


def test_open_with_str_path(doc: CfbIO) -> None:
    assert doc.root.name == "Root Entry"


def test_open_with_pathlib_path() -> None:
    assert CfbIO(Path("tests/data/simple.doc")).root.name == "Root Entry"


def test_context_manager() -> None:
    with CfbIO("tests/data/simple.doc") as doc:
        assert doc.root.name == "Root Entry"
        assert not doc.closed
    assert doc.closed


def test_repr(doc: CfbIO) -> None:
    assert repr(doc) == f'<CfbIO "{doc.name}">'


def test_len(doc: CfbIO) -> None:
    assert len(doc) == 7


def test_getitem_by_name(doc: CfbIO) -> None:
    assert doc["1Table"].name == "1Table"


def test_getitem_by_id(doc: CfbIO) -> None:
    assert doc[0] is doc.root
