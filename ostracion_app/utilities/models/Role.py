""" Role.py
    Class to handle 'role' database rows.
"""

from ostracion_app.utilities.models.DictableObject import DictableObject


class Role(DictableObject):
    namedFields = ['role_id', 'description', 'system']

    def __init__(self, **kwargs):
        """Standard 'DictableObject' init."""
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def __repr__(self):
        return '<Role "%s" (%s)>' % (self.role_id, self.description)

    def __lt__(self, other):
        return (
            (self.system == 0, self.role_id)
            < (other.system == 0, other.role_id)
        )
