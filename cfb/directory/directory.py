"""CFB directory structure."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

__all__ = ["Directory"]

from ..constants import ENDOFCHAIN
from ..exceptions import CfbDefect
from .entry import Entry, RootEntry

if TYPE_CHECKING:
    from ..io import CfbIO


class Directory(dict[int, Entry]):
    """Dictionary-based accessor for the internal CFB directory structure."""

    def __init__(self, source: CfbIO) -> None:
        super().__init__()
        self._name_cache: dict[str, int] = {}
        self.source = source
        self[0] = self.source.root

    def __del__(self) -> None:
        del self.source

    def read(self) -> None:
        """Eagerly load all directory entries.

        The directory is lazy-loaded by default; call this method to traverse
        the full tree up front.
        """
        root = cast(RootEntry, self[0])
        stack: list[Entry | None] = [root.child]
        while stack:
            current = stack.pop()
            if current is None:
                continue
            if current.right:
                stack.append(current.right)
            if current.left:
                stack.append(current.left)

        self[0].seek(0)

    def __getitem__(self, entry_id: int) -> Entry:
        """Return the directory entry for *entry_id*, loading it on first access.

        Raises :class:`TypeError` if *entry_id* is not an integer.
        Raises :class:`KeyError` if no entry exists at that ID.
        """
        if not isinstance(entry_id, int):
            raise TypeError(
                "Entry ID must be an integer; use by_name() to look up by name."
            )

        if entry_id in self:
            return super().__getitem__(entry_id)

        sector_size = self.source.header.sector_size // 128
        sector = self.source.header.directory_sector_start

        current = 0
        while (current + 1) * sector_size <= entry_id and sector != ENDOFCHAIN:
            sector = self.source.next_fat(sector)
            current += 1

        position = (sector + 1) << self.source.header.sector_shift
        position += (entry_id - current * sector_size) * 128

        if position >= self.source.size:
            raise KeyError(entry_id)

        try:
            instance = Entry(entry_id, self.source, position)
        except CfbDefect:
            raise KeyError(entry_id) from None

        self[entry_id] = instance
        self._name_cache[instance.name] = entry_id

        return instance

    def by_name(self, name: str) -> Entry:
        """Look up a directory entry by name using the CFB red-black tree.

        Results are cached after the first lookup.
        Raises :class:`KeyError` if no entry with that name exists.
        """
        if name in self._name_cache:
            return self[self._name_cache[name]]

        if self.source.root.name == name:
            return self.source.root
        current = self.source.root.child

        while current:
            if len(current.name) < len(name):
                current = current.right
            elif len(current.name) > len(name):
                current = current.left
            elif current.name < name:
                current = current.right
            elif current.name > name:
                current = current.left
            else:
                return current

        raise KeyError(name)
