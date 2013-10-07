from io import BytesIO
from unittest import TestCase

from cfb.exceptions import MaybeDefected, ErrorDefect, FatalDefect
from cfb.header import Header


class SourceMock(BytesIO, MaybeDefected):
    def __init__(self, value="", raise_if=ErrorDefect):
        super(SourceMock, self).__init__(value)
        MaybeDefected.__init__(self, raise_if=raise_if)

    def append(self, data):
        self.write(data)
        self.seek(0)

        return self

    def erase(self, till=0):
        self.seek(till)
        self.truncate(0)

        return self


class MyTestCase(TestCase):
    def test_errors(self):
        source = SourceMock()

        self.assertRaises(FatalDefect, Header, source)
        self.assertRaises(FatalDefect, Header, source.append("12345678"))

        self.assertRaises(ErrorDefect, Header,
                          source.erase().append(0xd0cf11e0a1b11ae1))
