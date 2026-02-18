"""CfbIO — the primary entry point for reading CFB files."""

from functools import cached_property
from io import FileIO
from os import fstat
from pathlib import Path
from typing import Self

from .constants import ENDOFCHAIN
from .directory import Directory
from .directory.entry import Entry, RootEntry
from .exceptions import ErrorDefect, MaybeDefected
from .header import Header
from .helpers import ByteHelpers

__all__ = ["CfbIO"]


class CfbIO(FileIO, MaybeDefected, ByteHelpers):
    """Read-only IO object for Microsoft Compound File Binary Format files.

    Provides access to the internal directory structure and entry streams.
    Entries are lazy-loaded by default; pass ``lazy=False`` to eagerly read
    the full directory tree on open.

    Supports use as a context manager::

        with CfbIO("document.doc") as doc:
            print(doc.root.name)
    """

    def __init__(
        self,
        name: str | Path,
        raise_if: type[ErrorDefect] = ErrorDefect,
        lazy: bool = False,
    ) -> None:
        super().__init__(str(name), mode="rb")
        MaybeDefected.__init__(self, raise_if=raise_if)

        self.size = fstat(self.fileno()).st_size
        self.header = Header(self)

        self.directory = Directory(self)
        if not lazy:
            self.directory.read()

    def __del__(self) -> None:
        self.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    @cached_property
    def root(self) -> RootEntry:
        """The root entry of the CFB directory tree."""
        sector = self.header.directory_sector_start
        position = (sector + 1) << self.header.sector_shift
        return RootEntry(self, position)

    def next_fat(self, current: int) -> int:
        """Return the next FAT sector for *current*.

        Intended for internal use only.
        """
        sector_size = self.header.sector_size // 4
        block = current // sector_size
        difat_position = 76

        if block >= 109:
            block -= 109
            sector = self.header.difat_sector_start

            while block >= sector_size:
                position = (sector + 1) << self.header.sector_shift
                position += self.header.sector_size - 4
                sector = self.get_long(position)
                block -= sector_size - 1

            difat_position = (sector + 1) << self.header.sector_shift
        fat_sector = self.get_long(difat_position + block * 4)

        fat_position = (fat_sector + 1) << self.header.sector_shift
        fat_position += (current % sector_size) * 4

        return self.get_long(fat_position)

    def next_minifat(self, current: int) -> int:
        """Return the next mini-FAT sector for *current*.

        Intended for internal use only.
        """
        position = 0
        sector_size = self.header.sector_size // 4
        sector = self.header.minifat_sector_start

        while sector != ENDOFCHAIN and (position + 1) * sector_size <= current:
            sector = self.next_fat(sector)
            position += 1

        if sector == ENDOFCHAIN:
            return ENDOFCHAIN

        minifat_position = (sector + 1) << self.header.sector_shift
        minifat_position += (current - position * sector_size) * 4

        return self.get_long(minifat_position)

    def __getitem__(self, item: str | int) -> Entry:
        """Look up a directory entry by integer ID or by name."""
        if isinstance(item, str):
            return self.directory.by_name(item)
        return self.directory[item]

    def __len__(self) -> int:
        return len(self.directory)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} "{self.name}">'
