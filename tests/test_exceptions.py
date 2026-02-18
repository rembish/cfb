import warnings

import pytest

from cfb.exceptions import ErrorDefect, FatalDefect, MaybeDefected


class TestMaybeDefected:
    def test_fatal_always_raises(self) -> None:
        defected = MaybeDefected(raise_if=ErrorDefect)
        with pytest.raises(FatalDefect):
            defected._fatal("Fatal!")

    def test_error_raises_at_threshold(self) -> None:
        defected = MaybeDefected(raise_if=ErrorDefect)
        with pytest.raises(ErrorDefect):
            defected._error("Error!")

    def test_warning_below_threshold_warns(self) -> None:
        defected = MaybeDefected(raise_if=ErrorDefect)
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            with pytest.raises(SyntaxWarning):
                defected._warning("Warning!")
