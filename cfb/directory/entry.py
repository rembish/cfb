"""CFB directory entry structures."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from os import SEEK_CUR, SEEK_END, SEEK_SET
from re import UNICODE, search
from struct import error as UnpackError
from struct import unpack
from typing import TYPE_CHECKING

from ..constants import (
    ENDOFCHAIN,
    MAXREGSID,
    NOSTREAM,
    ROOT,
    STORAGE,
    STREAM,
    UNALLOCATED,
)
from ..exceptions import MaybeDefected
from ..helpers import ByteHelpers, Guid, cached_property, from_filetime

if TYPE_CHECKING:
    from ..io import CfbIO

__all__ = ["SEEK_CUR", "SEEK_END", "SEEK_SET", "Entry", "RootEntry"]


class Entry(MaybeDefected, ByteHelpers):
    """File-like object providing access to a single CFB directory entry stream."""

    def __init__(self, entry_id: int, source: CfbIO, position: int) -> None:
        super().__init__(source.minimum_defect)

        self.id = entry_id
        self.source = source

        self.source.seek(position)
        try:
            (
                name,
                name_length,
                self.type,
                self.color,
                self.left_sibling_id,
                self.right_sibling_id,
                self.child_id,
                clsid,
                self.state_bits,
                creation_time,
                modified_time,
                self.sector_start,
                self.size,
            ) = unpack("<64sHBBLLL16sLQQLQ", self.source.read(128))

            try:
                self.name = name[:name_length].decode("utf-16").rstrip("\0")
            except UnicodeDecodeError:
                self._error("Bad Directory Entry name, possibly truncated.")

            if search(r"[/\\:!]", self.name, UNICODE):
                self._warning(
                    "The following characters are illegal and MUST NOT be part "
                    "of the name: '/', '\\', ':', '!'."
                )

            if self.type not in (UNALLOCATED, STORAGE, STREAM, ROOT):
                self._error(
                    "This field MUST be 0x00, 0x01, 0x02, or 0x05, depending "
                    "on the actual type of object. All other values are not valid."
                )
            elif self.type == UNALLOCATED:
                self._error("Cannot create a Directory Entry for an unallocated slot.")

            if self.color not in (0x00, 0x01):
                self._warning(
                    "This field MUST be 0x00 (red) or 0x01 (black). "
                    "All other values are not valid."
                )

            if MAXREGSID < self.left_sibling_id < NOSTREAM:
                self._warning(
                    "This field contains the Stream ID of the left sibling. "
                    "If there is no left sibling, the field MUST be set to "
                    "NOSTREAM (0xFFFFFFFF)."
                )
                self.left_sibling_id = NOSTREAM
            if MAXREGSID < self.right_sibling_id < NOSTREAM:
                self._warning(
                    "This field contains the Stream ID of the right sibling. "
                    "If there is no right sibling, the field MUST be set to "
                    "NOSTREAM (0xFFFFFFFF)."
                )
                self.right_sibling_id = NOSTREAM
            if MAXREGSID < self.child_id < NOSTREAM:
                self._warning(
                    "This field contains the Stream ID of a child object. "
                    "If there is no child object, the field MUST be set to "
                    "NOSTREAM (0xFFFFFFFF)."
                )
                self.child_id = NOSTREAM

            self.clsid = Guid(clsid)

            self.creation_time: datetime | None = from_filetime(creation_time)
            self.modified_time: datetime | None = from_filetime(modified_time)

            if self.source.header.version[0] == 3 and self.size > 0x80000000:
                self._error(
                    "For a version 3 compound file 512-byte sector size, "
                    "the value of this field MUST be less than or equal to 0x80000000."
                )

            self._is_mini = (
                self.type != ROOT and self.size < self.source.header.cutoff_size
            )

            self._position = 0
            self._position_in_sector = 0
            self._source_position = self.source.tell()
            self._sector_number = self.sector_start

            self.next_sector: Callable[[int], int] = (
                self.source.next_minifat if self._is_mini else self.source.next_fat
            )

            self.seek(0)
        except UnpackError:
            self._fatal("Bad Directory Entry header.")

    def __del__(self) -> None:
        del self.source

    def __repr__(self) -> str:
        name = self.__class__.__name__
        return f'<{name}[{self.id}] "{self.name}" of {self.source!r}>'

    @cached_property
    def sector_size(self) -> int:
        """Sector size for this entry (mini-sector or full sector)."""
        header = self.source.header
        return header.mini_sector_size if self._is_mini else header.sector_size

    @cached_property
    def sector_shift(self) -> int:
        """Sector shift for this entry (``sector_size == 2 ** sector_shift``)."""
        header = self.source.header
        return header.mini_sector_shift if self._is_mini else header.sector_shift

    @cached_property
    def left(self) -> Entry | None:
        """Left sibling entry, or ``None`` if absent."""
        return (
            self.source.directory[self.left_sibling_id]
            if self.left_sibling_id != NOSTREAM
            else None
        )

    @cached_property
    def right(self) -> Entry | None:
        """Right sibling entry, or ``None`` if absent."""
        return (
            self.source.directory[self.right_sibling_id]
            if self.right_sibling_id != NOSTREAM
            else None
        )

    @cached_property
    def stream(self) -> CfbIO | RootEntry:
        """Data source for this entry.

        Mini-stream entries read from the root entry; others read directly
        from the CFB file.
        """
        return self.source.root if self._is_mini else self.source

    def read(self, size: int | None = None) -> bytes:
        """Read *size* bytes from the current position.

        If *size* is ``None`` or negative, read until the end of the entry.
        """
        if self._is_mini:
            self.seek(self._position)
        else:
            self.source.seek(self._source_position)
        if not size or size < 0:
            size = self.size - self.tell()

        data = b""
        while len(data) < size:
            if self.tell() > self.size:
                break
            if self._sector_number == ENDOFCHAIN:
                break

            to_read = size - len(data)
            to_end = self.sector_size - self._position_in_sector
            to_do = min(to_read, to_end)
            data += self.stream.read(to_do)

            self._position += to_do
            self._source_position = self.source.tell()

            if to_read >= to_end:
                self._position_in_sector = 0
                self._sector_number = self.next_sector(self._sector_number)
                position = (
                    self._sector_number + int(not self._is_mini)
                ) << self.sector_shift
                self.stream.seek(position)
            else:
                self._position_in_sector += to_do

        return data

    def seek(self, offset: int, whence: int = SEEK_SET) -> int:
        """Seek to *offset* within this entry's stream.

        *whence* follows the usual ``os`` constants: ``SEEK_SET``, ``SEEK_CUR``,
        ``SEEK_END``.
        """
        if whence == SEEK_CUR:
            offset += self.tell()
        elif whence == SEEK_END:
            offset = self.size - offset

        self._position = offset
        self._sector_number = self.sector_start
        current = 0

        while (
            self._sector_number != ENDOFCHAIN
            and (current + 1) * self.sector_size < offset
        ):
            self._sector_number = self.next_sector(self._sector_number)
            current += 1

        self._position_in_sector = offset - current * self.sector_size

        position = (self._sector_number + int(not self._is_mini)) << self.sector_shift
        position += self._position_in_sector

        self.stream.seek(position)
        self._source_position = self.source.tell()
        return self.tell()

    def tell(self) -> int:
        """Return the current position within this entry's stream."""
        return self._position


class RootEntry(Entry):
    """The root directory entry; has a single child and no siblings."""

    def __init__(self, source: CfbIO, position: int) -> None:
        super().__init__(0, source, position)

    @cached_property
    def child(self) -> Entry | None:
        """The single child entry of the root, or ``None`` if the directory is empty."""
        if self.child_id == NOSTREAM:
            return None
        # For the root entry, stream is always the CfbIO source, never a mini-stream.
        return self.stream.directory[self.child_id]  # type: ignore[union-attr]

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} of {self.source!r}>"
