""" Ticket.py
    Class to represent all types of ticket as rows from DB.
"""

from ostracion_app.utilities.models.DictableObject import DictableObject


class Ticket(DictableObject):
    namedFields = ['ticket_id', 'name', 'security_code', 'username',
                   'issue_date', 'expiration_date', 'multiplicity',
                   'target_type', 'metadata', 'last_redeemed',
                   'times_redeemed']

    def __init__(self, **kwargs):
        """ Standard 'DictableObject' init."""
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def __repr__(self):
        return '<Ticket[%s]:%s >' % (self.ticket_id, self.target_type)
