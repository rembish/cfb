"""Internal CFB format constants."""

from .helpers import Guid

__all__ = [
    "ENDOFCHAIN",
    "GUID_NULL",
    "MAXREGSID",
    "NOSTREAM",
    "ROOT",
    "STORAGE",
    "STREAM",
    "UNALLOCATED",
]

MAXREGSID = 0xFFFFFFFA
ENDOFCHAIN = 0xFFFFFFFE
NOSTREAM = 0xFFFFFFFF

UNALLOCATED = 0x00
STORAGE = 0x01
STREAM = 0x02
ROOT = 0x05

GUID_NULL = Guid(b"\x00" * 16)
