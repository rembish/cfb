""" Internal directory structure """
from six import integer_types

from cfb.constants import ENDOFCHAIN
from cfb.directory.entry import Entry
from cfb.exceptions import CfbDefect

__all__ = ['Directory']


class Directory(dict):
    """
    Provides dictionary access to internal directory structure.
    """
    def __init__(self, source):
        super(Directory, self).__init__()
        self._name_cache = {}

        self.source = source
        self[0] = self.source.root

    def __del__(self):
        del self.source

    def read(self):
        """
        This module is lazy-loaded by default. You can read all internal
        structure by calling this method.
        """
        stack = [self[0].child]
        while stack:
            current = stack.pop()
            if current.right:
                stack.append(current.right)
            if current.left:
                stack.append(current.left)

        self[0].seek(0)

    def __getitem__(self, entry_id):
        """
        Accessing directory entries by their IDs. Raises KeyError if there are
        no entries with wanted ID. BTW, first time you want to access new
        not loaded yet entry, directory will seek for it in file and store
        it in own dictionary. Next time it uses "cached" way.
        """
        if not isinstance(entry_id, integer_types):
            raise TypeError("EntryId should be integer, use by_name() method "
                            "to access Directory Entries by name.")

        if entry_id in self:
            return super(Directory, self).__getitem__(entry_id)

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
            raise KeyError(entry_id)

        self[entry_id] = instance
        self._name_cache[instance.name] = entry_id

        return instance

    def by_name(self, name):
        """
        In many cases you want to access directory not by it's ID, but by
        it's name. This method implements red-black search method, which
        internally uses CFB format. Also this method has internal name cache
        to speed up 2nd+ named accesses.
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
