""" Compound File Binary Format IO module (currently read-only) """
from io import FileIO
from os import fstat
from six import string_types

from cfb.constants import ENDOFCHAIN
from cfb.directory import Directory
from cfb.directory.entry import RootEntry
from cfb.exceptions import MaybeDefected, ErrorDefect
from cfb.header import Header
from cfb.helpers import ByteHelpers, cached

__all__ = ["CfbIO"]


class CfbIO(FileIO, MaybeDefected, ByteHelpers):
    """
    Creates IO (currently read-only) object for accessing internal structure
    of Microsoft Compound File Binary Format Files.
    """
    # pylint: disable=R0904
    def __init__(self, name, raise_if=ErrorDefect, lazy=False):
        super(CfbIO, self).__init__(name, mode='rb')
        MaybeDefected.__init__(self, raise_if=raise_if)

        self.size = fstat(self.fileno()).st_size
        self.header = Header(self)

        self.directory = Directory(self)
        if not lazy:
            self.directory.read()

    def __del__(self):
        self.close()

    @cached
    def root(self):
        """ Property provides access to root object in CFB. """
        sector = self.header.directory_sector_start
        position = (sector + 1) << self.header.sector_shift
        return RootEntry(self, position)

    def next_fat(self, current):
        """
        Helper gives you seekable position of next FAT sector. Should not be
        called from external code.
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

    def next_minifat(self, current):
        """
        Helpers provides access to next mini-FAT sector and returns it's
        seekable position. Should not be called from external code.
        """
        position = 0
        sector_size = self.header.sector_size // 4
        sector = self.header.minifat_sector_start

        while sector != ENDOFCHAIN and (current + 1) * sector_size <= current:
            sector = self.next_fat(sector)
            position += 1

        if sector == ENDOFCHAIN:
            return ENDOFCHAIN

        minifat_position = (sector + 1) << self.header.sector_shift
        minifat_position += (current - position * sector_size) * 4

        return self.get_long(minifat_position)

    def __getitem__(self, item):
        """ You can access Directory Entries by ID (integer) or by name """
        if isinstance(item, string_types):
            return self.directory.by_name(item)
        return self.directory[item]

    def __len__(self):
        return len(self.directory)

    def __repr__(self):
        return '<%s "%s">' % (self.__class__.__name__, self.name)
