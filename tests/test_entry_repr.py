"""Tests for Entry.__repr__."""

from cfb import CfbIO


def test_entry_repr(doc: CfbIO) -> None:
    entry = doc["1Table"]
    assert repr(entry) == f'<Entry[3] "1Table" of {doc!r}>'


def test_root_repr(doc: CfbIO) -> None:
    assert repr(doc[0]) == f"<RootEntry of {doc!r}>"
