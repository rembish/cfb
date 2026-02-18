"""Tests for cfb.directory."""

import pytest

from cfb import CfbIO


def test_directory_source_and_root(doc: CfbIO) -> None:
    assert doc.directory.source is doc
    assert doc.directory[0] is doc.root


def test_directory_full_load(doc: CfbIO) -> None:
    # Root Entry, CompObj, Ole, 1Table, SummaryInformation, WordDocument,
    # and DocumentSummaryInformation — 7 entries total.
    assert len(doc.directory) == 7


def test_directory_out_of_range(doc: CfbIO) -> None:
    with pytest.raises(KeyError):
        _ = doc.directory[8]


def test_directory_by_name(doc: CfbIO) -> None:
    assert doc.directory.by_name("\005SummaryInformation").id == 4
    assert doc.directory.by_name("Root Entry") is doc.directory[0]


def test_directory_lazy_by_name(lazy_doc: CfbIO) -> None:
    assert lazy_doc.directory.by_name("1Table").name == "1Table"
    with pytest.raises(KeyError):
        lazy_doc.directory.by_name("2Table")


def test_directory_integer_key_required(lazy_doc: CfbIO) -> None:
    with pytest.raises(KeyError):
        _ = lazy_doc.directory[-1]
    with pytest.raises(TypeError):
        _ = lazy_doc.directory["Foo"]  # type: ignore[call-overload]


def test_directory_by_name_type_error(lazy_doc: CfbIO) -> None:
    with pytest.raises(TypeError):
        lazy_doc.directory.by_name(10)  # type: ignore[arg-type]


def test_directory_by_name_not_found_with_diacritics(lazy_doc: CfbIO) -> None:
    with pytest.raises(KeyError):
        lazy_doc.directory.by_name("Héllo, wörld!")


def test_directory_by_name_left_traversal(lazy_doc: CfbIO) -> None:
    # "0Table" has the same length as "1Table" but sorts before it, so the
    # red-black tree traversal must go left (directory.py line 105).
    with pytest.raises(KeyError):
        lazy_doc.directory.by_name("0Table")
