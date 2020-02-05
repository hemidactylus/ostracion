""" BoxRolePermision.py
    Class to represent a 'box role permission' DB row.
"""

from ostracion_app.utilities.models.DictableObject import DictableObject


class BoxRolePermission(DictableObject):
    namedFields = ['box_id', 'role_class', 'role_id', 'r', 'w', 'c']

    def __init__(self, **kwargs):
        """ Standard 'DictableObject' init
        """
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def __repr__(self):
        return '<BoxRolePermission (%s ! %s/%s): %s%s%s >' % (
            self.box_id,
            self.role_class,
            self.role_id,
            'R' if self.r else '-',
            'W' if self.w else '-',
            'C' if self.c else '-',
        )

    def roleKey(self):
        return (self.role_class, self.role_id)

    def display(self):
        return '%s/%s[%s%s%s]' % (
            self.role_class,
            self.role_id,
            'R' if self.r else '-',
            'W' if self.w else '-',
            'C' if self.c else '-',
        )

    def booleanBit(self, permissionBit):
        return getattr(self, permissionBit) != 0

    def __lt__(self, other):
        return (self.role_class, self.role_id).__lt__(
            (other.role_class, other.role_id)
        )

    def __gt__(self, other):
        return (self.role_class, self.role_id).__gr__(
            (other.role_class, other.role_id)
        )
