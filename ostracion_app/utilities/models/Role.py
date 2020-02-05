""" Role.py
    Class to handle 'role' database rows.
"""

from ostracion_app.utilities.models.DictableObject import DictableObject

_roleClassSortingIndex = {
    'system': 0,
    'app': 1,
    'manual': 2,
}


class Role(DictableObject):
    namedFields = ['role_id', 'description', 'role_class',
                   'can_box', 'can_user', 'can_delete']

    def __init__(self, **kwargs):
        """Standard 'DictableObject' init."""
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def roleKey(self):
        return (self.role_class, self.role_id)

    def __repr__(self):
        return '<Role "%s/%s" (%s)>' % (
            self.role_class,
            self.role_id,
            self.description,
        )

    def sortableTuple(self):
        return (
            _roleClassSortingIndex.get(self.role_class, 3),
            self.description.lower(),
        )

    def __lt__(self, other):
        return self.sortableTuple().__lt__(other.sortableTuple())
