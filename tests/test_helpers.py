from datetime import datetime
from uuid import UUID
from six import b, BytesIO
from time import time
from unittest import TestCase

from cfb.helpers import ByteHelpers, Guid, cached, from_filetime


class ByteHelpersTestCase(TestCase):
    def test_no_subclass(self):
        me = ByteHelpers()

        self.assertRaises(NotImplementedError, me.read)
        self.assertRaises(NotImplementedError, me.get_byte, 0)
        self.assertRaises(NotImplementedError, me.get_short, 1)
        self.assertRaises(NotImplementedError, me.get_long, 10)

    def test_subclass(self):
        class Foo(BytesIO, ByteHelpers):
            pass

        me = Foo(b('Compound Binary Format'))

        self.assertEqual(me.get_byte(0), ord('C'))
        self.assertEqual(me.get_short(3), ord('o') * 256 + ord('p'))
        self.assertEqual(me.get_long(9),
                         ord('a') * 256 ** 3 + ord('n') * 256 ** 2 +
                         ord('i') * 256 + ord('B'))


class GuidTestCase(TestCase):
    def test_main(self):
        me = Guid('abcdefghijklmnop')
        self.assertEqual(repr(me), '{61626364-6566-6768-696a-6b6c6d6e6f70}')

    def test_eq(self):
        me = Guid('abcdefghijklmnop')
        me_too = Guid('abcdefghijklmnop')

        self.assertEqual(me, me_too)

        but_not_me = UUID('61626364-6566-6768-696a-6b6c6d6e6f70')
        self.assertNotEqual(me, but_not_me)


class CachedTestCase(TestCase):
    def test_main(self):
        class Foo(object):
            def __init__(self):
                self.x = 0

            @cached
            def bar(self):
                self.x += 1
                return self.x

        me = Foo()
        self.assertEqual(me.bar, 1)
        self.assertEqual(me.bar, 1)
        self.assertEqual(me.x, 1)


class FiletimeTestCase(TestCase):
    def test_main(self):
        self.assertEqual(from_filetime(116444736000000000),
                         datetime(1970, 1, 1))

        current = time()
        filetime = current * 10000000 + 116444736000000000
        a = from_filetime(filetime)
        b = datetime.utcfromtimestamp(current)

        try:
            self.assertEqual(a, b)
        except AssertionError:
            # TODO Retest one microsecond leaking. Maybe bug.
            if (a - b).microseconds == 1 or (b - a).microseconds == 1:
                pass
            else:
                raise
