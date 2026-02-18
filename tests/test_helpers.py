from datetime import UTC, datetime, timedelta
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

    def test_filetime_epoch(self) -> None:
        # FILETIME tick 1 (100 ns) → 1601-01-01 00:00:00
        assert from_filetime(1) == datetime(1601, 1, 1)

    def test_zero_returns_none(self) -> None:
        assert from_filetime(0) is None

    def test_out_of_range_returns_none(self) -> None:
        # A value far beyond year 9999 must not raise.
        assert from_filetime(2**63 - 1) is None

    def test_pre_epoch_date(self) -> None:
        # A date before the Unix epoch (1601) must not raise.
        filetime = 100_000_000  # 10 seconds after FILETIME epoch
        assert from_filetime(filetime) == datetime(1601, 1, 1) + timedelta(seconds=10)

    def test_current_time(self) -> None:

        current = time()
        filetime = int(current * 10000000 + 116444736000000000)
        converted = from_filetime(filetime)
        assert converted is not None
        reference = datetime.fromtimestamp(current, tz=UTC).replace(tzinfo=None)

        delta = abs((converted - reference).total_seconds())
        # Allow at most one microsecond of rounding error.
        assert delta <= 0.000001
