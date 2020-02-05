""" UserRole.py
    Class abstracting the 'user-role relation' item from DB.
"""

from ostracion_app.utilities.models.DictableObject import DictableObject


class UserRole(DictableObject):
    namedFields = ['username', 'role_class', 'role_id']

    def __init__(self, **kwargs):
        """ Standard 'DictableObject' init."""
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def roleKey(self):
        return (self.role_class, self.role_id)

    def __repr__(self):
        return '<UserRole %s => %s/%s >' % (
            self.username,
            self.role_class,
            self.role_id,
        )
