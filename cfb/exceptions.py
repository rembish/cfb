from warnings import warn


class CfbError(Exception):
    pass


class CfbDefect(CfbError):
    pass


class WarningDefect(CfbDefect):
    pass


class ErrorDefect(WarningDefect):
    pass


class FatalDefect(ErrorDefect):
    pass


class MaybeDefected(object):
    def __init__(self, raise_if):
        super(MaybeDefected, self).__init__()
        self.minimum_defect = raise_if

    def raise_if(self, exception, message, *args, **kwargs):
        if isinstance(exception, self.minimum_defect):
            raise exception(*args, **kwargs)
        warn(message, SyntaxWarning, *args, **kwargs)

    def _fatal(self, *args, **kwargs):
        return self.raise_if(FatalDefect, *args, **kwargs)

    def _error(self, *args, **kwargs):
        return self.raise_if(ErrorDefect, *args, **kwargs)

    def _warning(self, *args, **kwargs):
        return self.raise_if(WarningDefect, *args, **kwargs)
