""" similarityTools.py
    Low-level tools to handle digram-based text similarity.

    In this context a 'DVector' is simply a vector of digrams,
    expressed as a (sparse) dictionary digram -> float,
    where digram is a string made of a pair of characters from
    'similarityAlphabet'.
"""

from collections import Counter
import json

from ostracion_app.utilities.tools.formatting import (
    stripToAscii,
    recursiveReplaceText,
    collapseSpaces,
)

separatorCharactersInIdentifiers = [
    ':',
    ',',
    '-',
    '_',
    ';',
    '.',
    '!',
    '?',
    '/',
    '\\',
]


similarityAlphabet = list('qwertyuiopasdfghjklzxcvbnm1234567890 ')
similarityDigrams = {
    '%s%s' % (c1, c2)
    for c1 in similarityAlphabet
    for c2 in similarityAlphabet
}


def normVector(vec):
    """Normalise a vector to L2-norm of one, handling empty/null vectors."""
    _norm = sum(i**2 for i in vec.values())**0.5
    if _norm > 0:
        return {k: v/_norm for k, v in vec.items()}
    else:
        return vec


def scalProd(v1, v2):
    """Regular scalar product between two vectors, optimised for DVectors."""
    _ck = v1.keys() & v2.keys()
    return sum(
        v1[k] * v2[k]
        for k in _ck
    )


def textToDVector(text):
    """ Make a DVector out of a text,
        i.e. a normalized vector with digram-components
        in an all-lowercase space spanned by similarityAlphabet**2.
    """
    _ltext = stripToAscii(
        collapseSpaces(
            recursiveReplaceText(
                text,
                separatorCharactersInIdentifiers,
                ' ',
            )
        ).strip().lower()
    )
    unnormDVector = {
        dg: v
        for dg, v in Counter(
            '%s%s' % (c1, c2)
            for c1, c2 in zip(
                _ltext[:-1],
                _ltext[1:],
            )
        ).items()
        if dg in similarityDigrams
    }
    return normVector(unnormDVector)


def serializeDVector(vec):
    """Serialization of a DVector to a string for DB storage."""
    return json.dumps(vec, sort_keys=True)


def deserializeDVector(vecS):
    """Deserialization of a DVector from e.g. DB storage."""
    return json.loads(vecS)


if __name__ == '__main__':
    import sys
    texts = sys.argv[1:]
    tMap = {
        i: {
            'text': t,
            'dvector': textToDVector(t),
        }
        for i, t in enumerate(texts)
    }
    #
    print('TEXTS')
    for i in range(len(tMap)):
        print('    [%2i] "%s"' % (i, tMap[i]['text']))
    print('\nSIMILARITIES')
    print('        ', end='')
    for i in range(len(tMap)):
        print('%8i' % i, end='')
    print('')
    for i in range(len(tMap)):
        print('%8i' % i, end='')
        for j in range(len(tMap)):
            sim = scalProd(
                tMap[i]['dvector'],
                tMap[j]['dvector'],
            )
            print('%8i' % int(1000 * sim + 0.5), end='')
        print('')
