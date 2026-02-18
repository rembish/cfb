"""Tests for Entry header parsing and field validation."""

from collections import namedtuple
from io import BytesIO

import pytest

from cfb.constants import ENDOFCHAIN
from cfb.directory.entry import Entry
from cfb.exceptions import ErrorDefect, FatalDefect, MaybeDefected, WarningDefect

# UTF-16LE "1Table\0" padded to 64 bytes, followed by the remaining entry fields.
_ENTRY_HEADER = (
    b"\x31\x00\x54\x00\x61\x00\x62\x00"
    b"\x6c\x00\x65\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00"
    # name_length=14, type=STREAM(2), color=red(0)
    # left=NOSTREAM, right=NOSTREAM, child=NOSTREAM
    b"\x0e\x00\x02\x00\xff\xff\xff\xff"
    b"\xff\xff\xff\xff\xff\xff\xff\xff"
    # clsid (16 bytes, all zero)
    b"\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00"
    # state_bits, creation_time, modified_time (all zero)
    b"\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00"
    # sector_start=3, size=0x691=1681
    b"\x00\x00\x00\x00\x03\x00\x00\x00"
    b"\x91\x06\x00\x00\x00\x00\x00\x00"
)


class MockCfbIO(BytesIO, MaybeDefected):
    """Minimal CFB IO mock for unit-testing Entry without a real file."""

    def __init__(self, value: bytes, raise_if: type = WarningDefect) -> None:
        super().__init__(value)
        MaybeDefected.__init__(self, raise_if=raise_if)

        header_like = namedtuple(
            "Header",
            "version cutoff_size mini_sector_size mini_sector_shift",
        )
        self.header = header_like(
            version=(3, 0),
            cutoff_size=0x00001000,
            mini_sector_size=2**0x0009,
            mini_sector_shift=0x0009,
        )
        self.root = BytesIO()
        self.default = value
        self.current = value

    def replace(self, start: int, replacement: bytes) -> "MockCfbIO":
        position = self.tell()
        self.current = (
            self.current[:start]
            + replacement
            + self.current[start + len(replacement) :]
        )
        self.seek(0)
        self.truncate(0)
        self.write(self.current)
        self.seek(position)
        return self

    def reset(self) -> "MockCfbIO":
        self.seek(0)
        self.truncate(0)
        self.write(self.default)
        self.current = self.default
        return self

    def next_minifat(self, x: int) -> int:
        return ENDOFCHAIN


@pytest.fixture
def source() -> MockCfbIO:
    """Return a fresh MockCfbIO pre-loaded with a valid entry header."""
    return MockCfbIO(_ENTRY_HEADER)


def test_bad_data_is_fatal() -> None:
    with pytest.raises(FatalDefect):
        Entry(3, MockCfbIO(b""), 0)


def test_illegal_name_char_is_warning(source: MockCfbIO) -> None:
    with pytest.raises(WarningDefect):
        Entry(3, source.replace(0, b"!"), 0)


def test_bad_name_length_is_error(source: MockCfbIO) -> None:
    with pytest.raises(ErrorDefect):
        Entry(3, source.replace(64, b"\x01"), 0)


def test_unallocated_type_is_error(source: MockCfbIO) -> None:
    with pytest.raises(ErrorDefect):
        Entry(3, source.replace(66, b"\x00"), 0)


def test_invalid_type_is_error(source: MockCfbIO) -> None:
    with pytest.raises(ErrorDefect):
        Entry(3, source.replace(66, b"\x03"), 0)


def test_invalid_color_is_warning(source: MockCfbIO) -> None:
    with pytest.raises(WarningDefect):
        Entry(3, source.replace(67, b"\x02"), 0)


@pytest.mark.parametrize("offset", [68, 72, 76])
def test_invalid_sibling_ids_are_warnings(source: MockCfbIO, offset: int) -> None:
    with pytest.raises(WarningDefect):
        Entry(3, source.replace(offset, b"\xfe\xff\xff\xff"), 0)


def test_oversized_stream_for_v3_is_error(source: MockCfbIO) -> None:
    with pytest.raises(ErrorDefect):
        Entry(3, source.replace(-8, b"\xff" * 8), 0)


def test_corrected_sibling_ids() -> None:
    source = (
        MockCfbIO(_ENTRY_HEADER, raise_if=ErrorDefect)
        .replace(68, b"\xfe\xff\xff\xff")
        .replace(72, b"\xfe\xff\xff\xff")
        .replace(76, b"\xfe\xff\xff\xff")
    )
    entry = Entry(3, source, 0)
    assert entry.left is None
    assert entry.right is None
    assert entry.child_id == 0xFFFFFFFF
