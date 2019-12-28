""" UserRole.py
    Class abstracting the 'user-role relation' item from DB.
"""

from ostracion_app.utilities.models.DictableObject import DictableObject


class UserRole(DictableObject):
    namedFields = ['username', 'role_id']

    def __init__(self, **kwargs):
        """ Standard 'DictableObject' init."""
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def __repr__(self):
        return '<UserRole %s => %s >' % (self.username, self.role_id)
