""" formatting.py
    Various formatting utilities
    (human-friendly file sizes, defaulting for web forms, string ascii
    normalization, and so on).
"""

import unicodedata

KBYTE = 1024.0

byteFormatClasses = [
    (0.85*KBYTE**1, KBYTE**0, 0, 'B'),
    (0.85*KBYTE**2, KBYTE**1, 1, 'KiB'),
    (0.85*KBYTE**3, KBYTE**2, 1, 'MiB'),
    (0.85*KBYTE**4, KBYTE**3, 1, 'GiB'),
    (0.85*KBYTE**5, KBYTE**4, 1, 'PiB'),
]


def formatBytesSize(nBytes):
    """ Convert a size in bytes into a human-friendly string with unit.
        Implemented with an ugly loop and mutable states.
    """
    for sizeCap, unit, nDecimals, unitName in byteFormatClasses:
        if nBytes <= sizeCap:
            return ('%%.%if %%s' % nDecimals) % (nBytes / unit, unitName)
    return (
        '%%.%if %%s' % byteFormatClasses[-1][2]
    ) % (
        nBytes / byteFormatClasses[-1][1], byteFormatClasses[-1][3]
    )


def applyDefault(value, default, additionalNulls=[]):
    """ Given an input value, convert it into
        a default if it falls into a set of 'nulls'.

        Useful for filling web-form values.
    """
    if (value is None or
            value == '' or
            any(value == an for an in additionalNulls)):
        return default
    else:
        return value


def transformIfNotEmpty(txt, tformer=lambda t: t):
    """ Given an input text, make it None if empty,
        otherwise *try* to apply a transformer.

        Useful for optional input of forms.
    """
    if txt == '':
        return None
    else:
        try:
            return tformer(txt)
        except Exception:
            return None


def stripToAscii(txt):
    """ Remove non-ascii characters, trying to map ordinary
        non-ascii into their counterpart (such as accented letters)."""
    return unicodedata.normalize(
        'NFD', txt.replace('_', ' ')
    ).encode('ascii', 'ignore').decode()


def recursiveReplaceText(txt, replacees, replacement):
    """ Apply a chain of replacements (old1, old2...) -> 'new' to a string,
        where all 'oldN' strings become 'new'.
    """
    if len(replacees) == 0:
        return txt
    else:
        return recursiveReplaceText(
            txt.replace(replacees[0], replacement),
            replacees[1:],
            replacement,
        )


def applyReplacementPairs(txt, reps):
    """ Apply a chain of replacements
            [(old1,new1), (old2,new2), ...]
        to a text.
    """
    if len(reps) == 0:
        return txt
    else:
        return applyReplacementPairs(
            txt.replace(reps[0][0], reps[0][1]),
            reps[1:],
        )


def collapseSpaces(txt):
    """ Reduce contiguous spaces to a single one.

        Note: poor implementation
        (could use regexes if performance is critical).
    """
    if '  ' in txt:
        return collapseSpaces(
            txt.replace('  ', ' ')
        )
    else:
        return txt
