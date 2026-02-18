from datetime import UTC, datetime
from functools import cached_property
from io import BytesIO
from time import time
from uuid import UUID

import pytest

from cfb.helpers import ByteHelpers, Guid, from_filetime


class TestByteHelpers:
    def test_not_implemented(self) -> None:
        helper = ByteHelpers()

        with pytest.raises(NotImplementedError):
            helper.read()
        with pytest.raises(NotImplementedError):
            helper.get_byte(0)
        with pytest.raises(NotImplementedError):
            helper.get_short(1)
        with pytest.raises(NotImplementedError):
            helper.get_long(10)

    def test_subclass(self) -> None:
        class ConcreteHelper(BytesIO, ByteHelpers):
            pass

        helper = ConcreteHelper(b"Compound Binary Format")

        assert helper.get_byte(0) == ord("C")
        assert helper.get_short(3) == ord("o") * 256 + ord("p")
        assert helper.get_long(9) == (
            ord("a") * 256**3 + ord("n") * 256**2 + ord("i") * 256 + ord("B")
        )


class TestGuid:
    def test_repr(self) -> None:
        guid = Guid("abcdefghijklmnop")
        assert repr(guid) == "{61626364-6566-6768-696a-6b6c6d6e6f70}"

    def test_eq_same_class(self) -> None:
        a = Guid("abcdefghijklmnop")
        b = Guid("abcdefghijklmnop")
        assert a == b

    def test_ne_different_class(self) -> None:
        guid = Guid("abcdefghijklmnop")
        uuid = UUID("61626364-6566-6768-696a-6b6c6d6e6f70")
        assert guid != uuid


class TestCachedProperty:
    def test_computed_once(self) -> None:
        class Counter:
            def __init__(self) -> None:
                self.calls = 0

            @cached_property
            def value(self) -> int:
                self.calls += 1
                return self.calls

        obj = Counter()
        assert obj.value == 1
        assert obj.value == 1  # second access — should not recompute
        assert obj.calls == 1


class TestFromFiletime:
    def test_unix_epoch(self) -> None:
        assert from_filetime(116444736000000000) == datetime(1970, 1, 1)

    def test_current_time(self) -> None:

        current = time()
        filetime = int(current * 10000000 + 116444736000000000)
        converted = from_filetime(filetime)
        reference = datetime.fromtimestamp(current, tz=UTC).replace(tzinfo=None)

        delta = abs((converted - reference).total_seconds())
        # Allow at most one microsecond of rounding error.
        assert delta <= 0.000001
