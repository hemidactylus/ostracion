""" dictTools.py
    Standard dict manipulations.
"""

from ostracion_app.utilities.tools.extraction import safeNone


def recursivelyMergeDictionaries(leadingMap, defaultMap):
    """ Deep-merge dictionaries without side-effects.

        General tool to merge dictionaries with leading overriding
        default. If subdicts are encountered (leadingMap leads),
        the procedure enters the substructure; otherwise
        (strings, lists, etc), in-block replacement is performed.

        No side-effects on the passed dictionaries.
    """
    if isinstance(leadingMap, dict):
        return {
            k: recursivelyMergeDictionaries(
                leadingMap[k],
                defaultMap=safeNone(defaultMap, {}).get(k),
            ) if k in leadingMap else defaultMap[k]
            for k in safeNone(defaultMap, {}).keys() | leadingMap.keys()
        }
    else:
        return leadingMap


def convertIterableToDictOfLists(iterable, keyer, valuer):
    """ Given an iterable of [T], a valuer T -> V
        and a keyer T -> K (with K a hashable type),
        a map {K -> [V]} is built which groups values by key.
    """
    dictionary = {}
    for item in iterable:
        key = keyer(item)
        if key not in dictionary:
            dictionary[key] = [valuer(item)]
        else:
            dictionary[key].append(valuer(item))
    return dictionary
