""" exceptions.py:
    custom exceptions for use within Ostracion.
    Also includes utilities to make these into a flashed message.
"""

from werkzeug.exceptions import HTTPException

import flask_api


class OstracionWarning(Exception):
    """A 'warning' exception."""
    def __init__(self, message):
        self.message = message
        super(OstracionWarning, self).__init__(message)

    def flashable(self):
        return {
            'msgClass': 'Warning',
            'msgHeading': 'Warning',
            'msgBody': self.message,
        }

    def getName(self):
        return self.__class__.__name__

    def __str__(self):
        return '%s(%r)' % (self.getName(), self.message)

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join('%s=%r' % (k, v) for k, v in self.__dict__.items())
        )


class OstracionError(Exception):
    """A 'proper error' exception."""
    def __init__(self, message):
        self.message = message
        super(OstracionError, self).__init__(message)

    def flashable(self):
        return {
            'msgClass': 'Error',
            'msgHeading': 'Error',
            'msgBody': self.message,
        }

    def getName(self):
        return self.__class__.__name__

    def __str__(self):
        return '%s(%r)' % (self.getName(), self.message)

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join('%s=%r' % (k, v) for k, v in self.__dict__.items())
        )


def exceptionToFlashable(error):
    """Makes any exception into a flashable error message."""
    if isinstance(error, OstracionWarning):
        return error.flashable()
    elif isinstance(error, OstracionError):
        return error.flashable()
    elif isinstance(error, HTTPException):
        errCode = error.code
        if any([
            flask_api.status.is_client_error(errCode),
            flask_api.status.is_server_error(errCode)
        ]):
            return {
                'msgClass': 'Error',
                'msgHeading': 'Error',
                'msgBody': str(error),
            }
        else:
            return {}
    else:
        # we do not show internals
        return {
            'msgClass': 'Error',
            'msgHeading': 'Error',
            'msgBody': 'a generic error occurred',
        }
