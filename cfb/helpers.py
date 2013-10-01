from datetime import datetime
from os import SEEK_SET
from struct import unpack
from uuid import UUID


class ByteHelpers(object):
    def seek(self, offset, whence=SEEK_SET):
        return NotImplemented

    def read(self, size=None):
        return NotImplemented

    def get_byte(self, start):
        self.seek(start)
        return unpack('<B', self.read(1))[0]

    def get_short(self, start):
        self.seek(start)
        return unpack('<H', self.read(2))[0]

    def get_long(self, start):
        self.seek(start)
        return unpack('<L', self.read(4))[0]


class Guid(UUID):
    def __init__(self, value):
        super(Guid, self).__init__(bytes=value)

    def __repr__(self):
        return '{%s}' % self


class cached(object):
    def __init__(self, function):
        self.function = function

    def __get__(self, instance, _):
        value = self.function(instance)
        setattr(instance, self.function.func_name, value)
        return value


def from_filetime(time):
    return datetime.utcfromtimestamp((time - 116444736000000000L) / 10000000)
