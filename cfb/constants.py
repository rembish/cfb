""" Internal CFB constants """
from six import b
from cfb.helpers import Guid

MAXREGSID = 0xfffffffa
ENDOFCHAIN = 0xfffffffe
NOSTREAM = 0xffffffff

UNALLOCATED = 0x00
STORAGE = 0x01
STREAM = 0x02
ROOT = 0x05

GUID_NULL = Guid(b('\0' * 16))
