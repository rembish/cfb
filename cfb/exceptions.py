""" Defects and module exceptions """
from warnings import warn


class CfbError(Exception):
    """ Any CFB module must produce subexception of this class """


class CfbDefect(CfbError):
    """
    Defect is a special error type. Many CFB files may have some shit in
    many-many supplementary fields, those fields are tested by reader and it
    produces error if error occurred. But in many cases we can skip non
    fatal defect and continue reading process.
    """


class WarningDefect(CfbDefect):
    """
    Simple defect. You can read current file with no future problems in
    most cases.
    """


class ErrorDefect(WarningDefect):
    """
    You are trying to read defected file. Reader will read data, but in
    some cases you will get crap in the end.
    """


class FatalDefect(ErrorDefect):
    """
    Reader found fatal defect in opened CFB file. You can continue only on
    your own risk.
    """


class MaybeDefected(object):
    """
    Mixin adds support of not fatal defects skipping for current object.
    """
    # pylint: disable=R0903

    def __init__(self, raise_if):
        self.minimum_defect = raise_if

    def raise_if(self, exception, message, *args, **kwargs):
        """
        If current exception has smaller priority than minimum, subclass of
        this class only warns user, otherwise normal exception will be raised.
        """
        if issubclass(exception, self.minimum_defect):
            raise exception(*args, **kwargs)
        warn(message, SyntaxWarning, *args, **kwargs)

    def _fatal(self, *args, **kwargs):
        """
        Try to raise fatal defect.
        """
        return self.raise_if(FatalDefect, *args, **kwargs)

    def _error(self, *args, **kwargs):
        """
        Try to raise standard not catastrophic defect.
        """
        return self.raise_if(ErrorDefect, *args, **kwargs)

    def _warning(self, *args, **kwargs):
        """
        Try to raise simple pass over defect.
        """
        return self.raise_if(WarningDefect, *args, **kwargs)
