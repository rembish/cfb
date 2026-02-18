"""Tests for cfb.helpers.from_filetime."""

from datetime import UTC, datetime, timedelta
from time import time

from cfb.helpers import from_filetime


def test_unix_epoch() -> None:
    assert from_filetime(116444736000000000) == datetime(1970, 1, 1)


def test_filetime_epoch() -> None:
    # FILETIME tick 1 (100 ns) -> 1601-01-01 00:00:00
    assert from_filetime(1) == datetime(1601, 1, 1)


def test_zero_returns_none() -> None:
    assert from_filetime(0) is None


def test_out_of_range_returns_none() -> None:
    # A value far beyond year 9999 must not raise.
    assert from_filetime(2**63 - 1) is None


def test_pre_epoch_date() -> None:
    # A date before the Unix epoch (1601) must not raise.
    filetime = 100_000_000  # 10 seconds after FILETIME epoch
    assert from_filetime(filetime) == datetime(1601, 1, 1) + timedelta(seconds=10)


def test_current_time() -> None:
    current = time()
    filetime = int(current * 10000000 + 116444736000000000)
    converted = from_filetime(filetime)
    assert converted is not None
    reference = datetime.fromtimestamp(current, tz=UTC).replace(tzinfo=None)

    delta = abs((converted - reference).total_seconds())
    # Allow at most one microsecond of rounding error.
    assert delta <= 0.000001
