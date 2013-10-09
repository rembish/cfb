from os import SEEK_END, SEEK_SET
from six import b, BytesIO
from unittest import TestCase

from cfb.exceptions import MaybeDefected, ErrorDefect, FatalDefect, \
    WarningDefect
from cfb.header import Header


class SourceMock(BytesIO, MaybeDefected):
    def __init__(self, value="", raise_if=ErrorDefect):
        super(SourceMock, self).__init__(b(value))
        MaybeDefected.__init__(self, raise_if=raise_if)

    def append(self, data):
        self.write(b(data))
        self.seek(0)

        return self

    def erase(self, till=0):
        self.seek(till, SEEK_END if till < 0 else SEEK_SET)
        self.truncate(self.tell())

        return self


class HeaderTestCase(TestCase):
    def test_main(self):
        source = SourceMock(raise_if=WarningDefect)

        self.assertRaises(FatalDefect, Header, source)
        self.assertRaises(FatalDefect, Header, source.append("12345678"))

        self.assertRaises(
            ErrorDefect, Header,
            source.erase().append("\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"))
        self.assertRaises(ErrorDefect, Header, source.append('1' * 16))
        self.assertRaises(FatalDefect, Header,
                          source.erase(-16).append('\0' * 16))

        self.assertRaises(ErrorDefect, Header,
                          source.append("1234567890"))
        self.assertRaises(WarningDefect, Header,
                          source.erase(-10).append("12\x04\x00345678"))
        self.assertRaises(FatalDefect, Header,
                          source.erase(-10).append("\x3e\x00\x04\x00123456"))
        self.assertRaises(ErrorDefect, Header,
                          source.erase(-6).append("\xfe\xff1234"))
        self.assertRaises(ErrorDefect, Header,
                          source.erase(-4).append("\x09\x0012"))
        self.assertRaises(
            ErrorDefect, Header,
            source.erase(-8).append("\x03\x00\xfe\xff\x0c\x0012"))
        self.assertRaises(ErrorDefect, Header,
                          source.erase(-4).append("\x09\x0012"))

        self.assertRaises(ErrorDefect, Header,
                          source.erase(-2).append("\x06\x00"))
        self.assertRaises(ErrorDefect, Header, source.append("1" * 6))

        self.assertRaises(FatalDefect, Header,
                          source.erase(-6).append('\0' * 6))

        self.assertRaises(ErrorDefect, Header,
                          source.append("1234" + '\0' * 32))
        self.assertRaises(ErrorDefect, Header,
                          source.erase(-36).append('\0' * 36))

        self.assertEqual(
            Header(source.erase(-20).append('\x00\x10' + '\0' * 18)).version,
            (3, 0x3e))
