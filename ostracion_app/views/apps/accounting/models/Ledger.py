""" Ledger.py
    Class to represent an accounting ledger.
"""

from ostracion_app.utilities.models.DictableObject import DictableObject


class Ledger(DictableObject):
    namedFields = ['ledger_id', 'name', 'description']

    def __init__(self, **kwargs):
        """ Standard 'DictableObject' init."""
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def __repr__(self):
        return '<Ledger[%s]:%s >' % (self.ledger_id, self.name)
