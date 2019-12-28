""" colorTools.py
    Tools to handle gradient shading
    used e.g. in some views for nice style.
"""


def prepareColorShadeMap(startHexColor, endHexColor, numShades):
    """ Calculate numShades equally-spaced hues of a gradient
        between two (hex-string-provided) colors,
        returning them as a map index -> hexcolor.
    """
    ct0 = colorStringToTuple(startHexColor)
    ct1 = colorStringToTuple(endHexColor)
    delta = [
        (c1 - c0) / max(1, numShades)
        for c0, c1 in zip(ct0, ct1)
    ]
    return {
        i: formatHexColor(
            c0 + i * d
            for c0, d in zip(ct0, delta)
        )
        for i in range(numShades)
    }


def colorStringToTuple(cS):
    """Make a hex-color-string into a triple of RGB integers."""
    _c = cS if cS[0] != '#' else cS[1:]
    r, g, b = (
        int(_c[(2 * i):((2 * i) + 2)], 16)
        for i in range(3)
    )
    return (r, g, b)


def formatHexColor(cT):
    """Make a triple of RGB integer into a pound-prefixed hex color string."""
    return '#%s' % (
        ''.join(
            '%02x' % min(max(0, int(c)), 255)
            for c in cT
        )
    )
