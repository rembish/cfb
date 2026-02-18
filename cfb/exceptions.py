"""Exceptions and defect-handling infrastructure for the cfb package."""

from __future__ import annotations

from typing import Any
from warnings import warn

__all__ = [
    "CfbDefect",
    "CfbError",
    "ErrorDefect",
    "FatalDefect",
    "MaybeDefected",
    "WarningDefect",
]


class CfbError(Exception):
    """Base exception for all cfb errors."""


class CfbDefect(CfbError):
    """Base class for format defects.

    Many CFB files contain non-conforming values in supplementary fields.
    Defects allow the reader to either skip minor violations or raise an
    exception, depending on the configured severity threshold.
    """


class WarningDefect(CfbDefect):
    """Minor defect. Reading can continue with no expected data loss."""


class ErrorDefect(WarningDefect):
    """Recoverable defect. Data may be read, but results could be incorrect."""


class FatalDefect(ErrorDefect):
    """Fatal defect. Continuing to read is only possible at the caller's risk."""


class MaybeDefected:
    """Mixin that adds severity-based defect handling to a class."""

    def __init__(self, raise_if: type[CfbDefect]) -> None:
        self.minimum_defect = raise_if

    def raise_if(
        self,
        exception: type[CfbDefect],
        message: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Raise *exception* if it meets the minimum severity, otherwise warn."""
        if issubclass(exception, self.minimum_defect):
            raise exception(*args, **kwargs)
        warn(message, SyntaxWarning, *args, **kwargs)

    def _fatal(self, *args: Any, **kwargs: Any) -> None:
        """Attempt to raise a :class:`FatalDefect`."""
        self.raise_if(FatalDefect, *args, **kwargs)

    def _error(self, *args: Any, **kwargs: Any) -> None:
        """Attempt to raise an :class:`ErrorDefect`."""
        self.raise_if(ErrorDefect, *args, **kwargs)

    def _warning(self, *args: Any, **kwargs: Any) -> None:
        """Attempt to raise a :class:`WarningDefect`."""
        self.raise_if(WarningDefect, *args, **kwargs)
