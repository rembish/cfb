""" CFB files header information """
from six import BytesIO, b
from struct import unpack, error as UnpackError
from cfb.constants import GUID_NULL

from cfb.exceptions import MaybeDefected
from cfb.helpers import Guid

__all__ = ['Header']


class Header(BytesIO, MaybeDefected):
    """
    Header object reads and provides information about opened CFB file.
    Many internal structures use its attributes to access wanted sectors and
    so on.
    """
    # pylint: disable=R0904, R0902
    signature = 0xd0cf11e0a1b11ae1

    def __init__(self, source):
        super(Header, self).__init__(source.read(76))
        MaybeDefected.__init__(self, raise_if=source.minimum_defect)

        try:
            if unpack('>Q', self.read(8))[0] != self.signature:
                raise UnpackError("Bad signature")
        except UnpackError:
            self._fatal('Identification signature for the compound file '
                        'structure, and MUST be set to the value 0xD0, '
                        '0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1.')

        try:
            self.clsid = Guid(self.read(16))
            if self.clsid != GUID_NULL:
                raise ValueError("Bad CLSID")
        except ValueError:
            self._error('Reserved and unused class ID that MUST be set to all '
                        'zeroes (CLSID_NULL).')

        try:
            minor, major, byte_order, self.sector_shift, \
                self.mini_sector_shift = unpack('<HHHHH', self.read(10))
            if major not in (3, 4):
                self._error('Version number for breaking changes. This field '
                            'MUST be set to either 0x0003 (version 3) or '
                            '0x0004 (version 4).')
            if minor != 0x003E:
                self._warning('Version number for non-breaking changes. This '
                              'field SHOULD be set to 0x003E if the major '
                              'version field is either 0x0003 or 0x0004.')

            if byte_order != 0xFFFE:
                self._fatal('This field MUST be set to 0xFFFE. This field is '
                            'a byte order mark for all integer fields, '
                            'specifying little-endian byte order.')

            if self.sector_shift not in (0x0009, 0x000C):
                self._error('This field MUST be set to 0x0009, or 0x000c, '
                            'depending on the Major Version field.')
            if self.sector_shift == 0x0009 and major != 3:
                self._error('If Major Version is 3, then the Sector Shift '
                            'MUST be 0x0009, specifying a sector size of '
                            '512 bytes.')
            if self.sector_shift == 0x000C and major != 4:
                self._error('If Major Version is 4, then the Sector Shift '
                            'MUST be 0x000C, specifying a sector size of '
                            '4096 bytes.')

            if self.mini_sector_shift != 0x0006:
                self._error('This field MUST be set to 0x0006. This field '
                            'specifies the sector size of the Mini Stream as '
                            'a power of 2.')

            if self.read(6) != b('\0' * 6):
                self._error('Reversed field MUST be set to all zeroes.')

            # TODO Add additional attributes checks
            (self.directory_sector_count, self.fat_sectors_count,
             self.directory_sector_start, self.transaction_count,
             self.cutoff_size, self.minifat_sector_start,
             self.minifat_sector_count, self.difat_sector_start,
             self.difat_sector_count) = unpack('<LLLLLLLLL', self.read(36))

            if major == 3 and self.directory_sector_count:
                self._error('If Major Version is 3, then the Number of '
                            'Directory Sectors MUST be zero. This field is '
                            'not supported for version 3 compound files.')

            if self.cutoff_size != 0x00001000:
                self._error('This integer field MUST be set to 0x00001000. '
                            'This field specifies the maximum size of a '
                            'user-defined data stream allocated from the '
                            'mini FAT and mini stream, and that cutoff is '
                            '4096 bytes. Any user-defined data stream larger '
                            'than or equal to this cutoff size must be '
                            'allocated as normal sectors from the FAT.')

            self.version = major, minor

            self.sector_size = 2 ** self.sector_shift
            self.mini_sector_size = 2 ** self.mini_sector_shift

        except UnpackError:
            self._fatal('Bad file attributes detected.')
