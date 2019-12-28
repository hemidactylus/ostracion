""" Box.py
    Class for 'box' objects from database.
"""

from uuid import uuid4

from ostracion_app.utilities.models.DictableObject import DictableObject

from ostracion_app.utilities.database.permissions import (
    updateRolePermissionsDownPath,
)

from ostracion_app.utilities.textSimilarity.similarityTools import (
    textToDVector,
    serializeDVector,
)


class Box(DictableObject):
    namedFields = [
        'box_id', 'box_name', 'parent_id', 'title', 'description',
        'icon_file_id', 'date', 'nature', 'creator_username',
        'icon_file_id_username', 'icon_mime_type', 'metadata_username',
        'dvector_box_name', 'dvector_title', 'dvector_description']

    def __init__(self, **kwargs):
        """ standard 'DictableObject' init
            but with some fields specially handled (defaults, etc).
        """
        if 'box_id' not in kwargs:
            kwargs['box_id'] = uuid4().hex
        for optF in {'icon_mime_type'}:
            if optF not in kwargs:
                kwargs[optF] = ''
        if 'dvector_box_name' not in kwargs:
            kwargs['dvector_box_name'] = serializeDVector(
                textToDVector(kwargs['box_name'])
            )
        if 'dvector_title' not in kwargs:
            kwargs['dvector_title'] = serializeDVector(
                textToDVector(kwargs['title'])
            )
        if 'dvector_description' not in kwargs:
            kwargs['dvector_description'] = serializeDVector(
                textToDVector(kwargs['description'])
            )
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )
        #
        self.permissions = []
        self.permissionHistory = []
        self.nativePermissionRoleIds = set()

    def __repr__(self):
        return '<Box "%s" (%s, id=%s)>' % (
            self.title, self.box_name, self.box_id
        )

    def getName(self):
        return self.box_name

    def getId(self):
        return self.box_id

    def updatePermissionData(self, fromBox, lastPermissionLayer):
        """ Update the permission details of the box
            with the structures obtained from higher in the path-from-root,
            taking care of:
                - merging permissions
                - stacking in history
                - keeping track of the explicit ('native') permissions set
                  for this box.
        """
        mergedLastLayerPermissions = updateRolePermissionsDownPath(
            fromBox.permissions,
            lastPermissionLayer,
        )
        self._setInheritedPermissions(mergedLastLayerPermissions)
        self._setPermissionHistory(
            fromBox.permissionHistory + [mergedLastLayerPermissions]
        )
        self._setNativePermissionRoleIds(lastPermissionLayer)

    def setPermissionData(self, permissions,
                          permissionHistory, lastPermissionLayer):
        """ Initialise a box-retrieval chain. with this permission details.
            This is the root-box starting case, after which
            'updatePermissionData' should be used.
        """
        self._setInheritedPermissions(permissions)
        self._setPermissionHistory(permissionHistory)
        self._setNativePermissionRoleIds(lastPermissionLayer)

    def _setInheritedPermissions(self, permissions):
        self.permissions = permissions

    def _setPermissionHistory(self, permissionHistory):
        self.permissionHistory = permissionHistory

    def _setNativePermissionRoleIds(self, lastPermissionLayer):
        self.nativePermissionRoleIds = {
            brp.role_id
            for brp in lastPermissionLayer
        }

    def listPermissions(self, mode=None):
        """ Give a list of permission-sets,
            return an iterable over all of them or
            the native/inherited ones only.

            mode = None / 'native' / 'inherited'
        """
        if mode is None:
            def selector(brp): return True
        elif mode == 'native':
            def selector(brp): return (
                brp.role_id in self.nativePermissionRoleIds
            )
        elif mode == 'inherited':
            def selector(brp): return (
                brp.role_id not in self.nativePermissionRoleIds
            )
        else:
            raise RuntimeError('unknown mode')
        for p in self.permissions:
            if selector(p):
                yield p
