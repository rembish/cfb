""" Few helper routines and classes for internal only uses """
from datetime import datetime
from os import SEEK_SET
from six import b, binary_type
from struct import unpack
from uuid import UUID


class ByteHelpers(object):
    """
    Mixin adds methods to read multi-byte integers from specified location.
    """
    def seek(self, offset, whence=SEEK_SET):
        """
        Your subclass should be seekable. You should redefine seek method to
        search specified position in working file.
        """
        # pylint: disable=W0613, R0201
        raise NotImplementedError

    def read(self, size=None):
        """
        Your subclass should be readable. You should redefine read method to
        read few bytes from working file.
        """
        # pylint: disable=W0613, R0201
        raise NotImplementedError

    def get_byte(self, start):
        """
        Returns one byte (as number) from starting position.
        """
        self.seek(start)
        return unpack('<B', self.read(1))[0]

    def get_short(self, start):
        """
        Returns one short (as 2-bytes number) from starting position.
        """
        self.seek(start)
        return unpack('<H', self.read(2))[0]

    def get_long(self, start):
        """
        Returns one long (as 4-bytes number) from starting position.
        """
        self.seek(start)
        return unpack('<L', self.read(4))[0]


class Guid(UUID):
    """
    UUID microsofication as GUID. Object are same, but have different
    repr format.
    """
    def __init__(self, value):
        super(Guid, self).__init__(
            bytes=value if isinstance(value, binary_type) else b(value))

    def __repr__(self):
        return '{%s}' % self

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.bytes == other.bytes

    def __ne__(self, other):
        return not self.__eq__(other)


class cached(object):
    """ Cached property helper """
    # pylint: disable=C0103, R0903
    def __init__(self, function):
        self.function = function

    def __get__(self, instance, _):
        value = self.function(instance)
        setattr(instance, self.function.__name__, value)
        return value


def from_filetime(time):
    """
    Convert Microsoft OLE time to datetime object
    116444736000000000 is January 1, 1970
    """
    return datetime.utcfromtimestamp((time - 116444736000000000) / 10000000.)
