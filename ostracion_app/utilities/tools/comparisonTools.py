""" comparisonTools.py
    Special comparison operators.
"""


def optionNumberLeq(nonable1, nonable2):
    """ Is nonable1 >= nonable2?

        A greater-than-or-equal-to operator
        between to 'option' numbers (i.e. which can be None).
        None is thought to play the role of 'infinity'.

        In particular:
            ALWAYS: None >= ANYTHING
            NEVER:  Finite >= None
    """
    if nonable1 is None:
        return True
    else:
        if nonable2 is None:
            return False
        else:
            return nonable1 >= nonable2
