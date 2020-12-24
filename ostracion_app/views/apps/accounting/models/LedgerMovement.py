""" LedgerMovement.py
    Class to represent a single transaction (movement) in a ledger.
"""

from ostracion_app.utilities.models.DictableObject import DictableObject


class LedgerMovement(DictableObject):
    namedFields = ['ledger_id', 'movement_id', 'category_id',
                   'subcategory_id', 'date', 'description', 'last_edit_date',
                   'last_edit_username']

    def __init__(self, **kwargs):
        """ Standard 'DictableObject' init."""
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def __repr__(self):
        return '<LedgerMovement[%s/%s]>' % (self.ledger_id, self.movement_id)
