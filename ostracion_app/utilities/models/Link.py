""" Link.py
    Class representing a 'Link' DB object.
"""

import json
from uuid import uuid4

from ostracion_app.utilities.models.DictableObject import DictableObject

from ostracion_app.utilities.textSimilarity.similarityTools import (
    textToDVector,
    serializeDVector,
)


class Link(DictableObject):
    namedFields = ['link_id', 'box_id', 'name', 'description',
                   'icon_file_id', 'date', 'creator_username',
                   'icon_file_id_username', 'icon_mime_type',
                   'metadata_username',
                   'dvector_name', 'dvector_description',
                   'target', 'metadata']

    def __init__(self, **kwargs):
        """Standard 'DictableObject' init plus some defaults."""
        if 'link_id' not in kwargs:
            kwargs['link_id'] = uuid4().hex
        if 'dvector_name' not in kwargs:
            kwargs['dvector_name'] = serializeDVector(
                textToDVector(kwargs['name'])
            )
        if 'dvector_description' not in kwargs:
            kwargs['dvector_description'] = serializeDVector(
                textToDVector(kwargs['description'])
            )
        for optF in {'icon_file_id', 'icon_mime_type'}:
            if optF not in kwargs:
                kwargs[optF] = ''
        if 'metadata_dict' in kwargs:
            kwargs['metadata'] = json.dumps(kwargs['metadata_dict'])
            del kwargs['metadata_dict']
        if 'metadata' not in kwargs:
            kwargs['metadata'] = '{}'
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def __repr__(self):
        return '<Link "%s" (%s -> "%s")>' % (
            self.link_id,
            self.name,
            self.target
        )

    def getName(self):
        return self.name

    def getId(self):
        return self.link_id

    def getMetadata(self):
        return json.loads(self.metadata)
