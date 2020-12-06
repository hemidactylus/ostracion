""" LedgerUser.py
    Class to represent the relation of a ledger and a user.
"""

from ostracion_app.utilities.models.DictableObject import DictableObject


class LedgerUser(DictableObject):
    namedFields = ['username', 'ledger_id']

    def __init__(self, **kwargs):
        """ Standard 'DictableObject' init."""
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def __repr__(self):
        return '<LedgerUser[%s/%s] >' % (self.username, self.ledger_id)
