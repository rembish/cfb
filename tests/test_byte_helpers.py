"""Tests for cfb.helpers.ByteHelpers."""

from io import BytesIO

import pytest

from cfb.helpers import ByteHelpers


def test_not_implemented() -> None:
    helper = ByteHelpers()

    with pytest.raises(NotImplementedError):
        helper.read()
    with pytest.raises(NotImplementedError):
        helper.get_byte(0)
    with pytest.raises(NotImplementedError):
        helper.get_short(1)
    with pytest.raises(NotImplementedError):
        helper.get_long(10)


def test_subclass() -> None:
    class ConcreteHelper(BytesIO, ByteHelpers):
        pass

    helper = ConcreteHelper(b"Compound Binary Format")

    assert helper.get_byte(0) == ord("C")
    assert helper.get_short(3) == ord("o") * 256 + ord("p")
    assert helper.get_long(9) == (
        ord("a") * 256**3 + ord("n") * 256**2 + ord("i") * 256 + ord("B")
    )
