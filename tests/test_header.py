"""Tests for cfb.header (Header validation)."""

from io import BytesIO
from os import SEEK_END, SEEK_SET

import pytest

from cfb.exceptions import ErrorDefect, FatalDefect, MaybeDefected, WarningDefect
from cfb.header import Header


class SourceMock(BytesIO, MaybeDefected):
    def __init__(self, value: bytes = b"", raise_if: type = ErrorDefect) -> None:
        super().__init__(value)
        MaybeDefected.__init__(self, raise_if=raise_if)

    def append(self, data: bytes) -> "SourceMock":
        self.write(data)
        self.seek(0)
        return self

    def erase(self, till: int = 0) -> "SourceMock":
        self.seek(till, SEEK_END if till < 0 else SEEK_SET)
        self.truncate(self.tell())
        return self


def test_header_validation() -> None:
    """Validate each field of the CFB header in sequence, building up valid state."""
    source = SourceMock(raise_if=WarningDefect)

    # Empty source — cannot read signature.
    with pytest.raises(FatalDefect):
        Header(source)

    # Truncated signature (only 8 bytes).
    with pytest.raises(FatalDefect):
        Header(source.append(b"12345678"))

    # Valid signature, but no CLSID follows.
    with pytest.raises(ErrorDefect):
        Header(source.erase().append(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"))

    # Non-null CLSID.
    with pytest.raises(ErrorDefect):
        Header(source.append(b"1" * 16))

    # Null CLSID (valid), but version fields are missing.
    with pytest.raises(FatalDefect):
        Header(source.erase(-16).append(b"\x00" * 16))

    # Invalid major version.
    with pytest.raises(ErrorDefect):
        Header(source.append(b"1234567890"))

    # Invalid minor version (should be 0x003E).
    with pytest.raises(WarningDefect):
        Header(source.erase(-10).append(b"12\x04\x00345678"))

    # Invalid byte order (must be 0xFFFE).
    with pytest.raises(FatalDefect):
        Header(source.erase(-10).append(b"\x3e\x00\x04\x00123456"))

    # Invalid sector shift.
    with pytest.raises(ErrorDefect):
        Header(source.erase(-6).append(b"\xfe\xff1234"))

    # Version 4 with sector_shift 0x0009 (should be 0x000C for v4).
    with pytest.raises(ErrorDefect):
        Header(source.erase(-4).append(b"\x09\x0012"))

    # Version 3 with sector_shift 0x000C (should be 0x0009 for v3).
    with pytest.raises(ErrorDefect):
        Header(source.erase(-8).append(b"\x03\x00\xfe\xff\x0c\x0012"))

    # Invalid mini sector shift (must be 0x0006).
    with pytest.raises(ErrorDefect):
        Header(source.erase(-4).append(b"\x09\x0012"))

    # Mini sector shift 0x0006 — valid so far; reserved bytes are non-zero.
    with pytest.raises(ErrorDefect):
        Header(source.erase(-2).append(b"\x06\x00"))
    with pytest.raises(ErrorDefect):
        Header(source.append(b"1" * 6))

    # Reserved bytes all zero — valid; sector counts/starts are missing.
    with pytest.raises(FatalDefect):
        Header(source.erase(-6).append(b"\x00" * 6))

    # Cutoff size wrong (first 4 bytes of 36-byte block).
    with pytest.raises(ErrorDefect):
        Header(source.append(b"1234" + b"\x00" * 32))

    # All-zero sector info — cutoff size 0 ≠ 0x1000.
    with pytest.raises(ErrorDefect):
        Header(source.erase(-36).append(b"\x00" * 36))

    # Set cutoff size to the required 0x1000 — header is now fully valid.
    header = Header(source.erase(-20).append(b"\x00\x10" + b"\x00" * 18))
    assert header.version == (3, 0x3E)
