"""Tests for cfb.directory."""

import warnings

import pytest

from cfb import CfbIO

_SIMPLE_DOC = "tests/data/simple.doc"


@pytest.fixture(autouse=True)
def suppress_warnings() -> None:
    warnings.simplefilter("ignore")


def test_directory_source_and_root() -> None:
    io = CfbIO(_SIMPLE_DOC)
    assert io.directory.source is io
    assert io.directory[0] is io.root


def test_directory_full_load() -> None:
    # Root Entry, CompObj, Ole, 1Table, SummaryInformation, WordDocument,
    # and DocumentSummaryInformation — 7 entries total.
    io = CfbIO(_SIMPLE_DOC)
    assert len(io.directory) == 7


def test_directory_out_of_range() -> None:
    io = CfbIO(_SIMPLE_DOC)
    with pytest.raises(KeyError):
        _ = io.directory[8]


def test_directory_by_name() -> None:
    io = CfbIO(_SIMPLE_DOC)
    assert io.directory.by_name("\005SummaryInformation").id == 4
    assert io.directory.by_name("Root Entry") is io.directory[0]


def test_directory_lazy_by_name() -> None:
    io = CfbIO(_SIMPLE_DOC, lazy=True)
    assert io.directory.by_name("1Table").name == "1Table"
    with pytest.raises(KeyError):
        io.directory.by_name("2Table")


def test_directory_integer_key_required() -> None:
    io = CfbIO(_SIMPLE_DOC, lazy=True)
    with pytest.raises(KeyError):
        _ = io.directory[-1]
    with pytest.raises(TypeError):
        _ = io.directory["Foo"]  # type: ignore[call-overload]


def test_directory_by_name_type_error() -> None:
    io = CfbIO(_SIMPLE_DOC, lazy=True)
    with pytest.raises(TypeError):
        io.directory.by_name(10)  # type: ignore[arg-type]


def test_directory_by_name_not_found_with_diacritics() -> None:
    io = CfbIO(_SIMPLE_DOC, lazy=True)
    with pytest.raises(KeyError):
        io.directory.by_name("Héllo, wörld!")


def test_directory_by_name_left_traversal() -> None:
    # "0Table" has the same length as "1Table" but sorts before it, so the
    # red-black tree traversal must go left (directory.py line 105).
    io = CfbIO(_SIMPLE_DOC, lazy=True)
    with pytest.raises(KeyError):
        io.directory.by_name("0Table")
