"""Utility classes and helpers for internal use only."""

from datetime import datetime, timedelta

__all__ = ["ByteHelpers", "Guid", "from_filetime"]
from os import SEEK_SET
from struct import unpack
from uuid import UUID


class ByteHelpers:
    """Mixin that adds methods to read multi-byte little-endian integers."""

    def seek(self, offset: int, whence: int = SEEK_SET) -> int:
        """Seek to a position in the buffer. Must be implemented by subclass."""
        raise NotImplementedError

    def read(self, size: int = -1) -> bytes:
        """Read bytes from the underlying buffer. Must be implemented by subclass."""
        raise NotImplementedError

    def get_byte(self, start: int) -> int:
        """Return one unsigned byte from the given offset."""
        self.seek(start)
        return int(unpack("<B", self.read(1))[0])

    def get_short(self, start: int) -> int:
        """Return one unsigned 16-bit integer (little-endian) from the given offset."""
        self.seek(start)
        return int(unpack("<H", self.read(2))[0])

    def get_long(self, start: int) -> int:
        """Return one unsigned 32-bit integer (little-endian) from the given offset."""
        self.seek(start)
        return int(unpack("<L", self.read(4))[0])


class Guid(UUID):
    """UUID subclass that formats itself as a Microsoft GUID string ``{...}``."""

    def __init__(self, value: bytes | str) -> None:
        super().__init__(
            bytes=value if isinstance(value, bytes) else value.encode("latin-1")
        )

    def __repr__(self) -> str:
        return f"{{{self}}}"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.bytes == other.bytes

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    __hash__ = UUID.__hash__


_FILETIME_EPOCH = datetime(1601, 1, 1)


def from_filetime(time: int) -> datetime | None:
    """Convert a Microsoft OLE FILETIME value to a naive UTC datetime.

    FILETIME counts 100-nanosecond intervals since January 1, 1601.
    Returns ``None`` for a zero value (meaning "not set") or any value that
    falls outside the representable datetime range.
    """
    if not time:
        return None
    try:
        return _FILETIME_EPOCH + timedelta(microseconds=time // 10)
    except (OverflowError, ValueError):
        return None
