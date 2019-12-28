""" extraction.py
    utilities to handle None conversions in extracting data.
"""


def safeNone(val, default=''):
    """Auto-convert None values into a default."""
    return val if val is not None else default
