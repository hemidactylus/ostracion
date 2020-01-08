""" File.py
    Class representing a 'file' DB object.
"""

from uuid import uuid4

from ostracion_app.utilities.models.DictableObject import DictableObject

from ostracion_app.utilities.textSimilarity.similarityTools import (
    textToDVector,
    serializeDVector,
)


class File(DictableObject):
    namedFields = ['file_id', 'box_id', 'name', 'description', 'icon_file_id',
                   'date', 'mime_type', 'textual_mode', 'type', 'size',
                   'creator_username', 'icon_file_id_username',
                   'icon_mime_type', 'metadata_username', 'editor_username',
                   'dvector_name', 'dvector_description']

    def __init__(self, **kwargs):
        """Standard 'DictableObject' init plus some defaults."""
        if 'file_id' not in kwargs:
            kwargs['file_id'] = uuid4().hex
        if 'dvector_name' not in kwargs:
            kwargs['dvector_name'] = serializeDVector(
                textToDVector(kwargs['name'])
            )
        if 'dvector_description' not in kwargs:
            kwargs['dvector_description'] = serializeDVector(
                textToDVector(kwargs['description'])
            )
        for optF in {'type', 'mime_type', 'size',
                     'icon_file_id', 'icon_mime_type'}:
            if optF not in kwargs:
                kwargs[optF] = ''
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def __repr__(self):
        return '<File "%s" (%s)>' % (self.file_id, self.name)

    def getName(self):
        return self.name

    def getId(self):
        return self.file_id
