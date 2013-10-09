""" Directory Entry structures """
from os import SEEK_SET, SEEK_CUR, SEEK_END
from re import search, UNICODE
from struct import unpack, error as UnpackError
from six import b

from cfb.constants import UNALLOCATED, STORAGE, STREAM, ROOT, MAXREGSID, \
    NOSTREAM, ENDOFCHAIN
from cfb.exceptions import MaybeDefected
from cfb.helpers import ByteHelpers, Guid, from_filetime, cached

__all__ = ['Entry', 'RootEntry', 'SEEK_CUR', 'SEEK_END', 'SEEK_SET']


class Entry(MaybeDefected, ByteHelpers):
    """
    General Entry class object. This is file-like object to access stored
    data in any Directory Entry in CFB file.
    """
    # pylint: disable=R0902
    def __init__(self, entry_id, source, position):
        super(Entry, self).__init__(source.minimum_defect)

        # pylint: disable=C0103
        self.id = entry_id
        self.source = source

        self.source.seek(position)
        try:
            (name, name_length, self.type, self.color, self.left_sibling_id,
             self.right_sibling_id, self.child_id, clsid, self.state_bits,
             creation_time, modified_time, self.sector_start, self.size) \
                = unpack('<64sHBBLLL16sLQQLQ', self.source.read(128))

            try:
                self.name = name[:name_length].decode("utf-16").rstrip("\0")
            except UnicodeDecodeError:
                self._error("Bad Directory Entry name, maybe truncated.")

            if search(r'[/\\:!]', self.name, UNICODE):
                self._warning("The following characters are illegal and MUST "
                              "NOT be part of the name: '/', '\', ':', '!'.")

            if self.type not in (UNALLOCATED, STORAGE, STREAM, ROOT):
                self._error("This field MUST be 0x00, 0x01, 0x02, or 0x05, "
                            "depending on the actual type of object. All "
                            "other values are not valid.")
            elif self.type == UNALLOCATED:
                self._error("Can't create Directory Entry for unallocated "
                            "place.")

            if self.color not in (0x00, 0x01):
                self._warning("This field MUST be 0x00 (red) or 0x01 (black). "
                              "All other values are not valid.")

            if MAXREGSID < self.left_sibling_id < NOSTREAM:
                self._warning("This field contains the Stream ID of the left "
                              "sibling. If there is no left sibling, the "
                              "field MUST be set to NOSTREAM (0xFFFFFFFF).")
                self.left_sibling_id = NOSTREAM
            if MAXREGSID < self.right_sibling_id < NOSTREAM:
                self._warning("This field contains the Stream ID of the right "
                              "sibling. If there is no right sibling, the "
                              "field MUST be set to NOSTREAM (0xFFFFFFFF).")
                self.right_sibling_id = NOSTREAM
            if MAXREGSID < self.child_id < NOSTREAM:
                self._warning("This field contains the Stream ID of a child "
                              "object. If there is no child object, then the "
                              "field MUST be set to NOSTREAM (0xFFFFFFFF).")
                self.child_id = NOSTREAM

            self.clsid = Guid(clsid)

            self.creation_time = from_filetime(creation_time) \
                if creation_time else None
            self.modified_time = from_filetime(modified_time) \
                if modified_time else None

            if self.source.header.version[0] == 3 and self.size > 0x80000000:
                self._error("For a version 3 compound file 512-byte sector "
                            "size, this value of this field MUST be less than "
                            "or equal to 0x80000000.")

            self._is_mini = self.type != ROOT \
                and self.size < self.source.header.cutoff_size

            self._position = 0
            self._position_in_sector = 0
            self._source_position = self.source.tell()

            self._sector_number = self.sector_start

            self.next_sector = self.source.next_minifat if self._is_mini \
                else self.source.next_fat

            self.seek(0)
        except UnpackError:
            self._fatal("Bad Directory Entry header")

    def __del__(self):
        del self.source

    def __repr__(self):
        return '<%s[%d] "%s" of %r>' % (
            self.__class__.__name__, self.id, self.name, self.source)

    @cached
    def sector_size(self):
        """
        Property with current sector size. CFB file can store normal sectors
        and smaller ones.
        """
        header = self.source.header
        return header.mini_sector_size if self._is_mini else header.sector_size

    @cached
    def sector_shift(self):
        """
        Property with current sector size shift. Actually sector size is
        2 ** sector shift
        """
        header = self.source.header
        return header.mini_sector_shift if self._is_mini \
            else header.sector_shift

    @cached
    def left(self):
        """
        Entry is left sibling of current directory entry
        """
        return self.source.directory[self.left_sibling_id] \
            if self.left_sibling_id != NOSTREAM else None

    @cached
    def right(self):
        """
        Entry is right sibling of current directory entry
        """
        return self.source.directory[self.right_sibling_id] \
            if self.right_sibling_id != NOSTREAM else None

    @cached
    def stream(self):
        """
        From what stream must current entry read data. Entries, which are
        stored in mini-FAT, use Root Entry as a data source, other entries
        use normal sectors in CFB file.
        """
        return self.source.root if self._is_mini else self.source

    def read(self, size=None):
        """
        Reads `size` bytes from current directory entry. If `size` is empty,
        it'll read all data till entry's end.
        """
        self.source.seek(self._source_position)
        if not size or size < 0:
            size = self.size - self.tell()

        data = b('')
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
                position = (self._sector_number + int(not self._is_mini)) \
                    << self.sector_shift
                self.stream.seek(position)
            else:
                self._position_in_sector += to_do

        return data

    def seek(self, offset, whence=SEEK_SET):
        """
        Seeks to specified `offset` position in current directory entry
        stream. `Whence` can be SEEK_SET - from entry's start, SEEK_CUR -
        from current position and SEEK_END - from entry's end. Constants are
        same with same stored `os` module.
        """
        if whence == SEEK_CUR:
            offset += self.tell()
        elif whence == SEEK_END:
            offset = self.size - offset

        self._position = offset
        self._sector_number = self.sector_start
        current = 0

        while self._sector_number != ENDOFCHAIN and \
                (current + 1) * self.sector_size < offset:
            self._sector_number = self.next_sector(self._sector_number)
            current += 1

        self._position_in_sector = offset - current * self.sector_size

        position = (self._sector_number + int(not self._is_mini)) \
            << self.sector_shift
        position += self._position_in_sector

        self.stream.seek(position)
        self._source_position = self.source.tell()
        return self.tell()

    def tell(self):
        """
        Gets current entry's position.
        """
        return self._position


class RootEntry(Entry):
    """ Root Entry is only one in opened file and only has one child. """
    def __init__(self, source, position):
        super(RootEntry, self).__init__(0, source, position)

    @cached
    def child(self):
        """
        Root entry object has only one child entry and no siblings.
        """
        return self.stream.directory[self.child_id] \
            if self.child_id != NOSTREAM else None

    def __repr__(self):
        return '<%s of %r>' % (self.__class__.__name__, self.source)
