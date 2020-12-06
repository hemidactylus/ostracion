""" Actor.py
    Class to represent an accounting actor.
"""

from ostracion_app.utilities.models.DictableObject import DictableObject


class Actor(DictableObject):
    namedFields = ['ledger_id', 'actor_id', 'name']

    def __init__(self, **kwargs):
        """ Standard 'DictableObject' init."""
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def __repr__(self):
        return '<Actor[%s/%s] >' % (self.ledger_id, self.actor_id)
