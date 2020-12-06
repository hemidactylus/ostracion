""" LedgerMovementContribution.py
    Class to represent the contribution of an actor to a single transaction
    (movement) in a ledger.
"""

from ostracion_app.utilities.models.DictableObject import DictableObject


class LedgerMovementContribution(DictableObject):
    namedFields = ['ledger_id', 'movement_id', 'actor_id', 'paid', 'due',
                   'proportion']

    def __init__(self, **kwargs):
        """ Standard 'DictableObject' init."""
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def __repr__(self):
        return '<LedgerMovementContribution[%s/%s/%s]>' % (
            self.ledger_id,
            self.movement_id,
            self.actor_id,
        )
