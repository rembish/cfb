from collections import namedtuple
from io import BytesIO
from unittest import TestCase
from warnings import simplefilter

from cfb.constants import ENDOFCHAIN
from cfb.directory.entry import Entry
from cfb.exceptions import MaybeDefected, WarningDefect


class MockCfbIO(BytesIO, MaybeDefected):
    def __init__(self, value):
        super(MockCfbIO, self).__init__(value)
        MaybeDefected.__init__(self, raise_if=WarningDefect)

        header_like = namedtuple("Header", "version cutoff_size "
                                           "mini_sector_size "
                                           "mini_sector_shift")
        self.header = header_like(version=(3, 0),
                                  cutoff_size=0x00001000,
                                  mini_sector_size=2 ** 0x0009,
                                  mini_sector_shift=0x0009)

        self.root = BytesIO()

    next_minifat = lambda x: ENDOFCHAIN


class EntryTestCase(TestCase):
    filename = "data/simple.doc"

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

        source = MockCfbIO(header)
        table = Entry(3, source, 0)
