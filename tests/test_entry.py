"""Tests for cfb.directory.entry."""

import warnings
from collections import namedtuple
from io import BytesIO

import pytest

from cfb import CfbIO
from cfb.constants import ENDOFCHAIN
from cfb.directory.entry import SEEK_CUR, SEEK_END, Entry
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


_SIMPLE_DOC = "tests/data/simple.doc"


@pytest.fixture
def suppress() -> None:
    warnings.simplefilter("ignore")


class TestEntryHeader:
    def test_bad_data_is_fatal(self) -> None:
        with pytest.raises(FatalDefect):
            Entry(3, MockCfbIO(b""), 0)

    def test_illegal_name_char_is_warning(self, suppress: None) -> None:
        source = MockCfbIO(_ENTRY_HEADER)
        with pytest.raises(WarningDefect):
            Entry(3, source.replace(0, b"!"), 0)

    def test_bad_name_length_is_error(self, suppress: None) -> None:
        source = MockCfbIO(_ENTRY_HEADER)
        with pytest.raises(ErrorDefect):
            Entry(3, source.reset().replace(64, b"\x01"), 0)

    def test_unallocated_type_is_error(self, suppress: None) -> None:
        source = MockCfbIO(_ENTRY_HEADER)
        with pytest.raises(ErrorDefect):
            Entry(3, source.reset().replace(66, b"\x00"), 0)

    def test_invalid_type_is_error(self, suppress: None) -> None:
        source = MockCfbIO(_ENTRY_HEADER)
        with pytest.raises(ErrorDefect):
            Entry(3, source.reset().replace(66, b"\x03"), 0)

    def test_invalid_color_is_warning(self, suppress: None) -> None:
        source = MockCfbIO(_ENTRY_HEADER)
        with pytest.raises(WarningDefect):
            Entry(3, source.reset().replace(67, b"\x02"), 0)

    def test_invalid_sibling_ids_are_warnings(self, suppress: None) -> None:
        source = MockCfbIO(_ENTRY_HEADER)
        for offset in (68, 72, 76):
            with pytest.raises(WarningDefect):
                Entry(3, source.reset().replace(offset, b"\xfe\xff\xff\xff"), 0)

    def test_oversized_stream_for_v3_is_error(self, suppress: None) -> None:
        source = MockCfbIO(_ENTRY_HEADER)
        with pytest.raises(ErrorDefect):
            Entry(3, source.reset().replace(-8, b"\xff" * 8), 0)

    def test_corrected_sibling_ids(self, suppress: None) -> None:
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


class TestEntryRepr:
    def test_entry_repr(self, suppress: None) -> None:
        io = CfbIO(_SIMPLE_DOC)
        entry = io["1Table"]
        assert repr(entry) == f'<Entry[3] "1Table" of <CfbIO "{_SIMPLE_DOC}">>'

    def test_root_repr(self, suppress: None) -> None:
        io = CfbIO(_SIMPLE_DOC)
        assert repr(io[0]) == f'<RootEntry of <CfbIO "{_SIMPLE_DOC}">>'


class TestEntryProperties:
    def test_mini_stream_entry(self, suppress: None) -> None:
        io = CfbIO(_SIMPLE_DOC)
        entry = io["1Table"]

        assert entry.next_sector == io.next_minifat
        assert entry.left is None
        assert entry.right is None
        with pytest.raises(AttributeError):
            _ = entry.child  # type: ignore[attr-defined]  # only on RootEntry
        assert entry.stream is io.root

    def test_sibling_links(self, suppress: None) -> None:
        io = CfbIO(_SIMPLE_DOC)
        entry = io[1]

        assert entry.left == io[2]
        assert entry.right == io["\005SummaryInformation"]

    def test_root_entry(self, suppress: None) -> None:
        io = CfbIO(_SIMPLE_DOC)
        root = io[0]

        assert io.root is root
        assert root.left is None
        assert root.right is None
        assert root.child == io[1]


class TestEntryIO:
    def test_seek_read_tell(self, suppress: None) -> None:
        io = CfbIO(_SIMPLE_DOC)
        entry = io["\001CompObj"]

        assert entry.tell() == 0
        assert entry.seek(32) == 32
        assert entry.read(23) == b"Microsoft Word-Dokument"
        assert entry.tell() == 32 + 23

        assert entry.seek(5, SEEK_CUR) == 32 + 23 + 5
        assert entry.read(9) == b"MSWordDoc"

        assert entry.seek(27, SEEK_END) == 16 * 5 - 1
        assert entry.read(8) == b"Document"

    def test_read_all(self, suppress: None) -> None:
        io = CfbIO(_SIMPLE_DOC)
        entry = io["\001CompObj"]

        entry.seek(0)
        data = entry.read()
        assert len(data) == entry.size
        assert b"Microsoft Word-Dokument" in data
        assert data.find(b"Microsoft Word-Dokument") == 32

    def test_read_past_end(self, suppress: None) -> None:
        io = CfbIO(_SIMPLE_DOC)
        entry = io["\001CompObj"]

        entry.seek(1024)
        assert entry.read(16) == b""
