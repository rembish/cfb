from unittest import TestCase
from warnings import catch_warnings
from cfb.exceptions import MaybeDefected, ErrorDefect, FatalDefect


class MaybeDefectedTestCase(TestCase):
    def test_main(self):
        me = MaybeDefected(raise_if=ErrorDefect)

        self.assertRaises(FatalDefect, me._fatal, "Fatal!")
        self.assertRaises(ErrorDefect, me._error, "Error!")

        with catch_warnings(record=True) as w:
            me._warning("Warning.")

            self.assertEqual(len(w), 1)
            self.assertEqual(w[-1].category, SyntaxWarning)
