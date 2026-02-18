"""Tests for cfb.exceptions (MaybeDefected hierarchy)."""

import warnings

import pytest

from cfb.exceptions import ErrorDefect, FatalDefect, MaybeDefected


@pytest.fixture
def defected() -> MaybeDefected:
    """Return a MaybeDefected instance that raises on ErrorDefect and above."""
    return MaybeDefected(raise_if=ErrorDefect)


def test_fatal_always_raises(defected: MaybeDefected) -> None:
    with pytest.raises(FatalDefect):
        defected._fatal("Fatal!")


def test_error_raises_at_threshold(defected: MaybeDefected) -> None:
    with pytest.raises(ErrorDefect):
        defected._error("Error!")


def test_warning_below_threshold_warns(defected: MaybeDefected) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(SyntaxWarning):
            defected._warning("Warning!")
