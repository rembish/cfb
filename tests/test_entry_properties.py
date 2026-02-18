"""Tests for Entry properties (next_sector, siblings, child, stream)."""

import pytest

from cfb import CfbIO


def test_mini_stream_entry(doc: CfbIO) -> None:
    entry = doc["1Table"]

    assert entry.next_sector == doc.next_minifat
    assert entry.left is None
    assert entry.right is None
    with pytest.raises(AttributeError):
        _ = entry.child  # type: ignore[attr-defined]  # only on RootEntry
    assert entry.stream is doc.root


def test_sibling_links(doc: CfbIO) -> None:
    entry = doc[1]

    assert entry.left == doc[2]
    assert entry.right == doc["\005SummaryInformation"]


def test_root_entry(doc: CfbIO) -> None:
    root = doc[0]

    assert doc.root is root
    assert root.left is None
    assert root.right is None
    assert root.child == doc[1]
