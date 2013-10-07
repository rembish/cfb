# coding=utf-8

from unittest import TestCase
from warnings import simplefilter

from cfb import CfbIO


class DirectoryTestCase(TestCase):
    def setUp(self):
        simplefilter("ignore")

    def test_main(self):
        owner = CfbIO("data/simple.doc")
        me = owner.directory

        self.assertEqual(me.source, owner)
        self.assertEqual(me[0], owner.root)

        # Root Entry, CompObj, Ole, 1Table, SummaryInformation, WordDocument
        # and DocumentSummaryInformation
        self.assertEqual(len(me), 7)

        self.assertRaises(KeyError, me.__getitem__, 8)
        self.assertEquals(me.by_name("\005SummaryInformation").id, 4)
        self.assertEquals(me.by_name("Root Entry"), me[0])

    def test_lazy(self):
        owner = CfbIO("data/simple.doc", lazy=True)
        me = owner.directory

        self.assertEquals(me.by_name("1Table").name, "1Table")
        self.assertRaises(KeyError, me.by_name, "2Table")

    def test_bad_indexes(self):
        owner = CfbIO("data/simple.doc", lazy=True)
        me = owner.directory

        self.assertRaises(KeyError, me.__getitem__, -1)
        self.assertRaises(TypeError, me.__getitem__, "Foo")
        self.assertRaises(TypeError, me.by_name, 10)
        self.assertRaises(KeyError, me.by_name, u'Здравствуй, мир!')
