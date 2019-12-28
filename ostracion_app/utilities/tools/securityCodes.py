""" securityCodes.py
    Cryptographically strong library to generate random strings
    (keys, constrained 'security codes' for tickets, etc).
"""

import os
import random

vowels = list('aeiou')
consonants = list('wrtypsdfghjklzxcvbnm')

skChars = list(
    '1234567890)(*&^%$#@!poiuytrewqlkjhgfdsamnbvcxzPOIUYTREWQLKJ'
    'HGFDSAMNBVCXZ;:/?.>,<`~\\[]{}')


def makeSecurityCode(nSyllables=6):
    """Generate a standard, pronounceable 'security code'."""
    def _randBiLetter():
        return '%s%s' % (
            consonants[ord(os.urandom(1)) % len(consonants)],
            vowels[ord(os.urandom(1)) % len(vowels)],
        )
    return (''.join(_randBiLetter() for _ in range(nSyllables))).upper()


def multiURandomInt(nBytes=3):
    """ Return a multi-byte obtained from a multiple
        read of the urandom high-entropy source."""
    return sum(
        256**i * b
        for i, b in enumerate(os.urandom(nBytes))
    )


def makeSecretKey(nChars=48):
    """Generate a hard secret key, e.g. for use in form encryption."""
    return ''.join(
        (skChars[multiURandomInt(2) % len(skChars)]) for _ in range(nChars)
    )
