""" setNaming.py
    Textual utilties to give human-friendly descriptions
    to set of characters.
"""

# ready-made blocks of characters with their name
charDescriptorSets = [
    (
        set('qwertyuioplkjhgfdsazxcvbnm'),
        'lowercase letters a-z',
    ),
    (
        set('qwertyuioplkjhgfdsazxcvbnm'.upper()),
        'uppercase letters A-Z',
    ),
    (
        set('1234567890'),
        'digits 0-9',
    ),
]

# hard-to-read single characters hence with a verbose name
namedCharMap = {
    '"': 'double-quote',
    '\'': 'single-quote',
    ' ': 'space',
}


def _checkCharDescriptor(residualSet, charDescSets):
    """ Recursively try and see if a whole named set is in the input
        set: if so, pile up its human-readable description and inspect
        the next ready-made sets.

        Returns a pair residualSet, nice-descriptions.
    """
    if len(charDescSets) == 0:
        return residualSet, []
    else:
        checkSet, thisDesc = charDescSets[0]
        if all(d in residualSet for d in checkSet):
            newSet = residualSet - checkSet
            newDesc = thisDesc
            furtherSet, furtherDesc = _checkCharDescriptor(
                newSet,
                charDescSets[1:],
            )
            return furtherSet, [thisDesc] + furtherDesc
        else:
            return _checkCharDescriptor(residualSet, charDescSets[1:])


def _nameChar(c):
    """Give a stringy description (either short or verbose) to a character."""
    if c in namedCharMap:
        return '"%s" (%s)' % (
            c,
            namedCharMap[c],
        )
    else:
        return '"%s"' % c


def _nameCharacters(residualSet):
    """Name a set of characters."""
    return [
        _nameChar(c)
        for c in sorted(residualSet)
    ]


def _colloquialJoinClauses(clauses):
    """Join strings with commas and 'and' for the last two."""
    return ', '.join(
        clauses[:-2]
        + [
            ' and '.join(clauses[-2:])
        ]
    )


def humanFriendlyDescribeCharacterSet(cSet):
    """Transform a character set in a nice description."""
    leftoverSet, descriptions = _checkCharDescriptor(cSet, charDescriptorSets)
    leftoverDescriptions = _nameCharacters(leftoverSet)
    return _colloquialJoinClauses(descriptions + leftoverDescriptions)


if __name__ == '__main__':
    _defaultCharSet = set(
        '1234567890qwertyuiopasdfghjklzxcvbnmPOIUYTREWQLKJHGFDSAMNBVCXZ_-.'
    )
    print(humanFriendlyDescribeCharacterSet(_defaultCharSet))
