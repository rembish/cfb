"""Tests for Entry seek/read/tell I/O operations."""

from cfb import CfbIO
from cfb.directory.entry import SEEK_CUR, SEEK_END


def test_seek_read_tell(doc: CfbIO) -> None:
    entry = doc["\001CompObj"]

    assert entry.tell() == 0
    assert entry.seek(32) == 32
    assert entry.read(23) == b"Microsoft Word-Dokument"
    assert entry.tell() == 32 + 23

    assert entry.seek(5, SEEK_CUR) == 32 + 23 + 5
    assert entry.read(9) == b"MSWordDoc"

    assert entry.seek(27, SEEK_END) == 16 * 5 - 1
    assert entry.read(8) == b"Document"


def test_read_all(doc: CfbIO) -> None:
    entry = doc["\001CompObj"]

    entry.seek(0)
    data = entry.read()
    assert len(data) == entry.size
    assert b"Microsoft Word-Dokument" in data
    assert data.find(b"Microsoft Word-Dokument") == 32


def test_read_past_end(doc: CfbIO) -> None:
    entry = doc["\001CompObj"]

    entry.seek(1024)
    assert entry.read(16) == b""


def test_seek_exact_sector_boundary(doc: CfbIO) -> None:
    """Regression: seeking to an exact multiple of sector_size must land in
    the correct sector, not one sector short.

    With the off-by-one bug (``< offset`` instead of ``<= offset`` in the
    while loop), seeking to offset = N * sector_size would stop at sector
    N-1 with ``_position_in_sector = sector_size``, pointing past the end
    of the wrong sector and causing read() to return garbage data.
    """
    entry = doc["WordDocument"]
    sector_size = doc.header.sector_size  # 512 for version-3 CFB

    # Offset 2048 = 4 * 512 is an exact sector boundary; at that position
    # the WordDocument stream contains "O\x00" (UTF-16-LE for the start of
    # "One two three four five.").
    entry.seek(4 * sector_size)
    assert entry.read(2) == b"O\x00"
