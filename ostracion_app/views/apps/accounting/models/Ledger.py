""" Ledger.py
    Class to represent an accounting ledger.
"""

from ostracion_app.utilities.models.DictableObject import DictableObject


class Ledger(DictableObject):
    namedFields = ['ledger_id', 'name', 'description', 'creator_username',
                   'creation_date',  'configuration_date', 'last_edit_date',
                   'last_edit_username', 'icon_file_id',
                   'icon_file_id_username', 'icon_mime_type']

    def __init__(self, **kwargs):
        """ Standard 'DictableObject' init."""
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def __repr__(self):
        return '<Ledger[%s]:%s>' % (self.ledger_id, self.name)
