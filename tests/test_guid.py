"""Tests for cfb.helpers.Guid."""

from uuid import UUID

from cfb.helpers import Guid


def test_repr() -> None:
    guid = Guid("abcdefghijklmnop")
    assert repr(guid) == "{61626364-6566-6768-696a-6b6c6d6e6f70}"


def test_eq_same_class() -> None:
    a = Guid("abcdefghijklmnop")
    b = Guid("abcdefghijklmnop")
    assert a == b


def test_ne_different_class() -> None:
    guid = Guid("abcdefghijklmnop")
    uuid = UUID("61626364-6566-6768-696a-6b6c6d6e6f70")
    assert guid != uuid
