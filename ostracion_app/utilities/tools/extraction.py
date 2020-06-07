""" extraction.py
    utilities to handle None conversions in extracting data.
"""

import urllib.parse


def safeNone(val, default=''):
    """Auto-convert None values into a default."""
    return val if val is not None else default


def safeInt(val, default=None):
    """Try to make a string into an Int and default to 'default'."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def safeUnquotePlus(val, default=None):
    """Try to urllib.parse.unquote_plus the input, defaulting to 'default'."""
    try:
        return urllib.parse.unquote_plus(val)
    except (ValueError, TypeError, AttributeError):
        return default
