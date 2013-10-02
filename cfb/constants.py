""" Internal CFB constants """
from sys import version_info

MAXREGSID = 0xfffffffa
ENDOFCHAIN = 0xfffffffe
NOSTREAM = 0xffffffff

UNALLOCATED = 0x00
STORAGE = 0x01
STREAM = 0x02
ROOT = 0x05

PY3 = version_info[0] == 3
