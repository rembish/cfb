from unittest import TestCase
from warnings import simplefilter
from cfb.exceptions import MaybeDefected, ErrorDefect, FatalDefect


class MaybeDefectedTestCase(TestCase):
    def test_main(self):
        me = MaybeDefected(raise_if=ErrorDefect)

        self.assertRaises(FatalDefect, me._fatal, "Fatal!")
        self.assertRaises(ErrorDefect, me._error, "Error!")

        simplefilter("error")
        self.assertRaises(SyntaxWarning, me._warning, "Warning!")
