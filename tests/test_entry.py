from collections import namedtuple
from six import BytesIO, b
from unittest import TestCase
from warnings import simplefilter

from cfb import CfbIO
from cfb.constants import ENDOFCHAIN
from cfb.directory.entry import Entry, SEEK_CUR, SEEK_END
from cfb.exceptions import MaybeDefected, WarningDefect, FatalDefect, \
    ErrorDefect


class MockCfbIO(BytesIO, MaybeDefected):
    def __init__(self, value, raise_if=WarningDefect):
        value = b(value)

        super(MockCfbIO, self).__init__(value)
        MaybeDefected.__init__(self, raise_if=raise_if)

        header_like = namedtuple("Header", "version cutoff_size "
                                           "mini_sector_size "
                                           "mini_sector_shift")
        self.header = header_like(version=(3, 0),
                                  cutoff_size=0x00001000,
                                  mini_sector_size=2 ** 0x0009,
                                  mini_sector_shift=0x0009)

        self.root = BytesIO()
        self.default = value
        self.current = value

    def replace(self, start, replacement):
        replacement = b(replacement)
        position = self.tell()
        self.current = self.current[:start] + replacement + \
                       self.current[start + len(replacement):]

        self.seek(0)
        self.truncate(0)
        self.write(self.current)
        self.seek(position)

        return self

    def reset(self):
        self.seek(0)
        self.truncate(0)
        self.write(self.default)
        self.current = self.default

        return self

    next_minifat = lambda x: ENDOFCHAIN


class EntryTestCase(TestCase):
    filename = "tests/data/simple.doc"

    def setUp(self):
        simplefilter("ignore")

    def test_header(self):
        header = "\x31\x00\x54\x00\x61\x00\x62\x00" \
                 "\x6c\x00\x65\x00\x00\x00\x00\x00" \
                 "\x00\x00\x00\x00\x00\x00\x00\x00" \
                 "\x00\x00\x00\x00\x00\x00\x00\x00" \
                 "\x00\x00\x00\x00\x00\x00\x00\x00" \
                 "\x00\x00\x00\x00\x00\x00\x00\x00" \
                 "\x00\x00\x00\x00\x00\x00\x00\x00" \
                 "\x00\x00\x00\x00\x00\x00\x00\x00" \
                 "\x0e\x00\x02\x00\xff\xff\xff\xff" \
                 "\xff\xff\xff\xff\xff\xff\xff\xff" \
                 "\x00\x00\x00\x00\x00\x00\x00\x00" \
                 "\x00\x00\x00\x00\x00\x00\x00\x00" \
                 "\x00\x00\x00\x00\x00\x00\x00\x00" \
                 "\x00\x00\x00\x00\x00\x00\x00\x00" \
                 "\x00\x00\x00\x00\x03\x00\x00\x00" \
                 "\x91\x06\x00\x00\x00\x00\x00\x00"

        self.assertRaises(FatalDefect, Entry, 3, MockCfbIO(""), 0)

        source = MockCfbIO(header)
        self.assertRaises(WarningDefect, Entry, 3, source.replace(0, "!"), 0)
        self.assertRaises(ErrorDefect, Entry, 3,
                          source.reset().replace(64, "\x01"), 0)

        self.assertRaises(ErrorDefect, Entry, 3,
                          source.reset().replace(66, "\x00"), 0)
        self.assertRaises(ErrorDefect, Entry, 3,
                          source.reset().replace(66, "\x03"), 0)
        self.assertRaises(WarningDefect, Entry, 3,
                          source.reset().replace(67, "\x02"), 0)

        self.assertRaises(WarningDefect, Entry, 3,
                          source.reset().replace(68, "\xfe\xff\xff\xff"), 0)
        self.assertRaises(WarningDefect, Entry, 3,
                          source.reset().replace(72, "\xfe\xff\xff\xff"), 0)
        self.assertRaises(WarningDefect, Entry, 3,
                          source.reset().replace(76, "\xfe\xff\xff\xff"), 0)

        self.assertRaises(ErrorDefect, Entry, 3,
                          source.reset().replace(-8, "\xff" * 8), 0)

        source = MockCfbIO(header, raise_if=ErrorDefect)\
            .replace(68, "\xfe\xff\xff\xff")\
            .replace(72, "\xfe\xff\xff\xff")\
            .replace(76, "\xfe\xff\xff\xff")
        me = Entry(3, source, 0)
        self.assertTrue(me.left is None)
        self.assertTrue(me.right is None)
        self.assertEqual(me.child_id, 0xffffffff)

    def test_repr(self):
        io = CfbIO(self.filename)
        me = io["1Table"]

        self.assertEqual(repr(me),
                         '<Entry[3] "1Table" of <CfbIO "%s">>' % self.filename)

    def test_properties(self):
        io = CfbIO(self.filename)
        me = io["1Table"]

        self.assertEqual(me.next_sector, io.next_minifat)
        self.assertTrue(me.left is None)
        self.assertTrue(me.right is None)
        self.assertRaises(AttributeError, me.__getattribute__, "child")
        self.assertEqual(me.stream, io.root)

        another = io[1]
        self.assertEqual(another.left, io[2])
        self.assertEqual(another.right, io["\005SummaryInformation"])

    def test_root(self):
        io = CfbIO(self.filename)
        me = io[0]

        self.assertEqual(io.root, me)
        self.assertEqual(repr(me),
                         '<RootEntry of <CfbIO "%s">>' % self.filename)
        self.assertTrue(me.left is None)
        self.assertTrue(me.right is None)
        self.assertEqual(me.child, io[1])

    def test_io(self):
        io = CfbIO(self.filename)
        me = io["\001CompObj"]

        self.assertEqual(me.tell(), 0)
        self.assertEqual(me.seek(32), 32)
        self.assertEqual(me.read(23), b('Microsoft Word-Dokument'))
        self.assertEqual(me.tell(), 32 + 23)
        self.assertEqual(me.seek(5, SEEK_CUR), 32 + 23 + 5)
        self.assertEqual(me.read(9), b('MSWordDoc'))
        self.assertEqual(me.seek(27, SEEK_END), 16 * 5 - 1)
        self.assertEqual(me.read(8), b('Document'))

        self.assertEqual(me.seek(0), 0)
        data = me.read()
        self.assertEqual(me.size, len(data))
        self.assertTrue(b('Microsoft Word-Dokument') in data)
        self.assertEqual(data.find(b('Microsoft Word-Dokument')), 32)

        self.assertEqual(me.seek(1024), 1024)
        self.assertEqual(me.read(16), b(''))
