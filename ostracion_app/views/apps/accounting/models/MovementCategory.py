""" MovementCategory.py
    Class to represent a movement category in a ledger.
"""

from ostracion_app.utilities.models.DictableObject import DictableObject


class MovementCategory(DictableObject):
    namedFields = ['ledger_id', 'category_id', 'name', 'sort_index']

    def __init__(self, **kwargs):
        """ Standard 'DictableObject' init."""
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def __repr__(self):
        return '<MovementCategory[%s/%s] >' % (
            self.ledger_id,
            self.category_id,
        )
