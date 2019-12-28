""" listTools.py
    Ordinary list manipulations.
"""


def orderPreservingUniquifyList(lst, keyer=lambda itm: itm):
    """ Given a list of elements, build a new, uniquified one:
        skip already-inserted items and returns
        a new, possibly shorter list.

        This is a generalised delete_duplicates, in that it allows
        to work on a list of non-hashable items [A1,A2,A3...]
        and the uniqueness acts on a generic keyer function
            keyer: A -> K       (K must be hashable)
        so that the resulting list guarantees unicity of
        the keyer applied to the surviving elements.
    """
    newL = []
    usedKeys = set()
    for itm in lst:
        itmKey = keyer(itm)
        if itmKey not in usedKeys:
            newL.append(itm)
            usedKeys.add(itmKey)
    return newL
