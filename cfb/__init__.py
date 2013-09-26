from datetime import datetime
from io import FileIO, BytesIO
from os import SEEK_CUR, SEEK_END, SEEK_SET, fstat
from re import search, UNICODE
from struct import unpack
from uuid import UUID

MAXREGSID = 0xfffffffa
ENDOFCHAIN = 0xfffffffe
NOSTREAM = 0xffffffff

UNALLOCATED = 0x00
STORAGE = 0x01
STREAM = 0x02
ROOT = 0x05


class cached(object):
    def __init__(self, function):
        self.function = function

    def __get__(self, instance, owner):
        if not instance:
            return self

        value = self.function(instance)
        setattr(instance, self.function.func_name, value)
        return value


def from_filetime(time):
    return datetime.utcfromtimestamp((time - 116444736000000000L) / 10000000)


class CfbError(Exception):
    pass


class CfbDefect(CfbError):
    pass


class FatalDefect(CfbDefect):
    pass


class ErrorDefect(CfbDefect):
    pass


class WarningDefect(CfbDefect):
    pass


class Guid(UUID):
    def __init__(self, value):
        super(Guid, self).__init__(bytes=value)

CLSID_NULL = Guid('\0' * 16)


class MaybeDefected(object):
    def raise_if(self, exception, *args, **kwargs):
        raise exception(*args, **kwargs)

    def _fatal(self, *args, **kwargs):
        return self.raise_if(FatalDefect, *args, **kwargs)

    def _error(self, *args, **kwargs):
        return self.raise_if(ErrorDefect, *args, **kwargs)

    def _warning(self, *args, **kwargs):
        return
        return self.raise_if(WarningDefect, *args, **kwargs)


class ByteHelpers(object):
    def get_byte(self, start):
        self.seek(start)
        return unpack('<B', self.read(1))[0]

    def get_short(self, start):
        self.seek(start)
        return unpack('<H', self.read(2))[0]

    def read_long(self):
        return unpack('<L', self.read(4))[0]


class Header(BytesIO, MaybeDefected):
    signature = 0xd0cf11e0a1b11ae1

    def __init__(self, data):
        super(Header, self).__init__(data)

        if unpack('>Q', self.read(8))[0] != self.signature:
            self._fatal('Identification signature for the compound file '
                        'structure, and MUST be set to the value 0xD0, '
                        '0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1.')

        self.clsid = Guid(self.read(16))
        if self.clsid != CLSID_NULL:
            self._error('Reserved and unused class ID that MUST be set to all '
                        'zeroes (CLSID_NULL).')

        minor, major, byte_order, self.sector_shift, self.mini_sector_shift = \
            unpack('<HHHHH', self.read(10))

        if major not in (3, 4):
            self._error('Version number for breaking changes. This field MUST '
                        'be set to either 0x0003 (version 3) or 0x0004 '
                        '(version 4).')
        if minor != 0x003E:
            self._warning('Version number for non-breaking changes. This '
                          'field SHOULD be set to 0x003E if the major version '
                          'field is either 0x0003 or 0x0004.')

        if byte_order != 0xFFFE:
            self._fatal('This field MUST be set to 0xFFFE. This field is a '
                        'byte order mark for all integer fields, specifying '
                        'little-endian byte order.')

        if self.sector_shift not in (0x0009, 0x000C):
            self._error('This field MUST be set to 0x0009, or 0x000c, '
                        'depending on the Major Version field.')
        if self.sector_shift == 0x0009 and major != 3:
            self._error('If Major Version is 3, then the Sector Shift MUST be '
                        '0x0009, specifying a sector size of 512 bytes.')
        if self.sector_shift == 0x000C and major != 4:
            self._error('If Major Version is 4, then the Sector Shift MUST be '
                        '0x000C, specifying a sector size of 4096 bytes.')

        if self.mini_sector_shift != 0x0006:
            self._error('This field MUST be set to 0x0006. This field '
                        'specifies the sector size of the Mini Stream as '
                        'a power of 2.')

        if self.read(6) != '\0' * 6:
            self._error('Reversed field MUST be set to all zeroes.')

        (self.directory_sector_count, self.fat_sectors_count,
         self.directory_sector_start, self.transaction_count,
         self.cutoff_size, self.minifat_sector_start,
         self.minifat_sector_count, self.difat_sector_start,
         self.difat_sector_count) = unpack('<LLLLLLLLL', self.read(36))

        if major == 3 and self.directory_sector_count:
            self._error('If Major Version is 3, then the Number of Directory '
                        'Sectors MUST be zero. This field is not supported '
                        'for version 3 compound files.')

        if self.cutoff_size != 0x00001000:
            self._error('This integer field MUST be set to 0x00001000. This '
                        'field specifies the maximum size of a user-defined '
                        'data stream allocated from the mini FAT and mini '
                        'stream, and that cutoff is 4096 bytes. Any '
                        'user-defined data stream larger than or equal to '
                        'this cutoff size must be allocated as normal sectors '
                        'from the FAT.')

        self.version = major, minor

        self.sector_size = 2 ** self.sector_shift
        self.mini_sector_size = 2 ** self.mini_sector_shift


class Entry(MaybeDefected, ByteHelpers):
    def __init__(self, entry_id, source, position):
        self.id = entry_id
        self.source = source

        self.source.seek(position)
        (name, name_length, self.type, self.color, self.left_sibling_id,
         self.right_sibling_id, self.child_id, clsid, self.state_bits,
         creation_time, modified_time, self.sector_start, self.size) \
            = unpack('<64sHBBLLL16sLQQLQ', self.source.read(128))

        self.name = name[:name_length].decode("utf-16").rstrip("\0")

        if search(r'[/\\:!]', self.name, UNICODE):
            self._warning("The following characters are illegal and MUST NOT "
                          "be part of the name: '/', '\', ':', '!'.")

        if self.type not in (UNALLOCATED, STORAGE, STREAM, ROOT):
            self._error("This field MUST be 0x00, 0x01, 0x02, or 0x05, "
                        "depending on the actual type of object. All other "
                        "values are not valid.")
        elif self.type == UNALLOCATED:
            self._error("Can't create Directory Entry for unallocated place.")

        if self.color not in (0x00, 0x01):
            self._warning("This field MUST be 0x00 (red) or 0x01 (black). "
                          "All other values are not valid.")

        if MAXREGSID < self.left_sibling_id < NOSTREAM:
            self._warning("This field contains the Stream ID of the left "
                          "sibling. If there is no left sibling, the field "
                          "MUST be set to NOSTREAM (0xFFFFFFFF).")
            self.left_sibling_id = NOSTREAM
        if MAXREGSID < self.right_sibling_id < NOSTREAM:
            self._warning("This field contains the Stream ID of the right "
                          "sibling. If there is no right sibling, the field "
                          "MUST be set to NOSTREAM (0xFFFFFFFF).")
            self.right_sibling_id = NOSTREAM
        if MAXREGSID < self.child_id < NOSTREAM:
            self._warning("This field contains the Stream ID of a child "
                          "object. If there is no child object, then the "
                          "field MUST be set to NOSTREAM (0xFFFFFFFF).")
            self.child_id = None

        self.clsid = Guid(clsid)

        self.creation_time = creation_time and from_filetime(creation_time)
        self.modified_time = modified_time and from_filetime(modified_time)

        if self.source.header.version[0] == 3 and self.size > 0x80000000:
            self._error("For a version 3 compound file 512-byte sector size, "
                        "this value of this field MUST be less than or equal "
                        "to 0x80000000.")

        self._is_mini = self.type != ROOT \
            and self.size < self.source.header.cutoff_size

        self._position = 0
        self._position_in_sector = 0

        self._sector_number = self.sector_start

        self.next_sector = self.source.next_minifat if self._is_mini \
            else self.source.next_fat

        self.seek(0)

    def __repr__(self):
        return '<%s "%s">' % (self.__class__.__name__, self.name)

    def __len__(self):
        return self.size

    @cached
    def sector_size(self):
        header = self.source.header
        return header.mini_sector_size if self._is_mini else header.sector_size

    @cached
    def sector_shift(self):
        header = self.source.header
        return header.mini_sector_shift if self._is_mini \
            else header.sector_shift

    @cached
    def left(self):
        return self.source.directory[self.left_sibling_id] \
            if self.left_sibling_id != NOSTREAM else None

    @cached
    def right(self):
        return self.source.directory[self.right_sibling_id] \
            if self.right_sibling_id != NOSTREAM else None

    @cached
    def stream(self):
        return self.source.root if self._is_mini else self.source

    def read(self, size=None):
        if not size or size < 0:
            size = self.size - self.tell()

        data = ""
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
            if to_read >= to_end:
                self._position_in_sector = 0

                self._sector_number = \
                    self.next_sector(self._sector_number)
                position = (self._sector_number + int(not self._is_mini)) \
                    << self.sector_shift
                self.stream.seek(position)
            else:
                self._position_in_sector += to_do

        return data[:size]

    def seek(self, offset, whence=SEEK_SET):
        if whence == SEEK_CUR:
            offset += self.tell()
        elif whence == SEEK_END:
            offset = self.size - offset

        self._position = offset
        self._sector_number = self.sector_start
        current_position = 0

        while self._sector_number != ENDOFCHAIN and \
                (current_position + 1) * self.sector_size < offset:
            self._sector_number = self.next_sector(self._sector_number)
            current_position += 1

        self._position_in_sector = offset - current_position * self.sector_size
        sector_position = \
            (self._sector_number + int(not self._is_mini)) << self.sector_shift
        sector_position += self._position_in_sector

        self.stream.seek(sector_position)

    def tell(self):
        return self._position


class RootEntry(Entry):
    def __init__(self, source, position):
        super(RootEntry, self).__init__(0, source, position)

    @cached
    def child(self):
        return self.stream.directory[self.child_id] \
            if self.child_id != NOSTREAM else None


class Directory(dict):
    def __init__(self, source):
        super(Directory, self).__init__()
        self._name_cache = {}

        self.source = source
        self[0] = self.source.root

    def read(self):
        stack = [self[0].child]
        while stack:
            current = stack.pop()
            if current.right:
                stack.append(current.right)
            if current.left:
                stack.append(current.left)

    def __getitem__(self, entry_id):
        if entry_id in self:
            return super(Directory, self).__getitem__(entry_id)

        sector_size = self.source.header.sector_size / 128
        sector = self.source.header.directory_sector_start

        current = 0
        while (current + 1) * sector_size <= entry_id and sector != ENDOFCHAIN:
            sector = self.source.next_fat(sector)
            current += 1

        position = (sector + 1) << self.source.header.sector_shift
        position += (entry_id - current * sector_size) * 128

        if position >= self.source.length:
            raise KeyError(entry_id)

        self[entry_id] = entry = Entry(entry_id, self.source, position)
        self._name_cache[entry.name] = entry_id

        return entry

    def by_name(self, name):
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
            elif cmp(current.name, name) < 0:
                current = current.right
            elif cmp(current.name, name) > 0:
                current = current.left
            else:
                return current

        raise KeyError(name)


class CfbIO(FileIO, MaybeDefected, ByteHelpers):
    def __init__(self, name):
        super(CfbIO, self).__init__(name, mode='rb')
        self.length = fstat(self.fileno()).st_size
        self.header = Header(self.read(76))

        self.directory = Directory(self)
        self.directory.read()

    @cached
    def root(self):
        sector = self.header.directory_sector_start
        position = (sector + 1) << self.header.sector_shift
        return RootEntry(self, position)

    def next_fat(self, current):
        sector_size = self.header.sector_size / 4
        block = current / sector_size

        if block < 109:
            self.seek(76 + block * 4)
        else:
            block -= 109
            sector = self.header.difat_sector_start

            while block >= sector_size:
                position = (sector + 1) << self.header.sector_shift
                self.seek(position + self.header.sector_size - 4)
                sector = self.read_long()
                block -= sector_size - 1

            position = (sector + 1) << self.header.sector_shift
            self.seek(position + block * 4)

        fat_sector = self.read_long()
        fat_position = (fat_sector + 1) << self.header.sector_shift
        self.seek(fat_position + (current % sector_size) * 4)

        return self.read_long()

    def next_minifat(self, current):
        position = 0
        sector_size = self.header.sector_size / 4
        sector = self.header.minifat_sector_start

        while sector != ENDOFCHAIN and (current+ 1) * sector_size <= current:
            sector = self.next_fat(sector)
            position += 1

        if sector == ENDOFCHAIN:
            return ENDOFCHAIN

        sector_position = (sector + 1) << self.header.sector_shift
        sector_position += (current - position * sector_size) * 4
        self.seek(sector_position)

        return self.read_long()

    def __getitem__(self, item):
        if isinstance(item, basestring):
            return self.directory.by_name(item)
        return self.directory[item]
