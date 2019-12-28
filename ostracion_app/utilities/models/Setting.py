""" Setting.py
    Class to represent all 'setting' items from DB.
"""

from ostracion_app.utilities.models.DictableObject import DictableObject


class Setting(DictableObject):
    namedFields = ['id', 'klass', 'type', 'value', 'title', 'description',
                   'default_value', 'metadata', 'group_id', 'group_title',
                   'ordering', 'group_ordering', 'icon_mime_type',
                   'default_icon_mime_type']

    def __init__(self, **kwargs):
        """ Standard 'DictableObject' init."""
        for optF in {'icon_mime_type', 'default_icon_mime_type'}:
            if optF not in kwargs:
                kwargs[optF] = ''
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def getName(self):
        return '%s (%s)' % (self.title, self.group_title)

    def __repr__(self):
        return '<Setting "%s" (%s)>' % (self.id, self.title)
