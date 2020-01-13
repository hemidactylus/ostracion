""" fileSystem.py
    Tools to access the on-DB filesystem, navigate it,
    operate on it, etc.

    Note for some functions we usually apply permission-based
    limitations, but if the parameter
        accountDeletionInProgress = True
    (which is passed to subsequent calls), permission
    restrictions are lifted and special actions are performed.
"""

from ostracion_app.utilities.models.Box import Box
from ostracion_app.utilities.models.File import File
from ostracion_app.utilities.models.Link import Link

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries,
)

from ostracion_app.utilities.database.sqliteEngine import (
    dbRetrieveRecordByKey,
    dbRetrieveRecordsByKey,
    dbAddRecordToTable,
    dbDeleteRecordsByKey,
    dbUpdateRecordOnTable,
)

from ostracion_app.utilities.database.permissions import (
    dbGetBoxRolePermissions,
    updateRolePermissionsDownPath,
    userHasPermission,
)

from ostracion_app.utilities.database.dbSchema import (
    dbSchema,
)

from ostracion_app.utilities.fileIO.physical import (
    fileIdToPath,
    flushFsDeleteQueue,
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)


def getBoxesFromParent(db, parentBox, user, accountDeletionInProgress=False):
    """ Return, as in Yield, all boxes in a given box:
        if boxes are not accessible, None's are returned instead
        (which is important for some callers as it tells them
        the parentBox has indeed sub-boxes, albeit invisible to user).
    """
    for boxDict in dbRetrieveRecordsByKey(
        db,
        'boxes',
        {'parent_id': parentBox.box_id},
        dbTablesDesc=dbSchema,
    ):
        #
        newPermissionLayer = list(
            dbGetBoxRolePermissions(db, boxDict['box_id'])
        )
        if accountDeletionInProgress or userHasPermission(
                db,
                user,
                parentBox.permissions,
                'r',
        ):
            thisBox = Box(**boxDict)
            thisBox.updatePermissionData(
                fromBox=parentBox,
                lastPermissionLayer=newPermissionLayer,
            )
            if accountDeletionInProgress or userHasPermission(
                    db,
                    user,
                    thisBox.permissions,
                    'r',
            ):
                yield thisBox
            else:
                yield None
        else:
            # the mere existence of not-visible-at-all boxes
            # must be reported, e.g. for the deletebox chain of calls
            yield None


def getRootBox(db):
    """ Return the root box with permissions set. """
    boxDict = dbRetrieveRecordByKey(
        db,
        'boxes',
        {'box_id': ''},
        dbTablesDesc=dbSchema,
    )
    rootBoxPermissions = list(dbGetBoxRolePermissions(db, ''))
    #
    thisBox = Box(**boxDict)
    thisBox.setPermissionData(
        permissions=rootBoxPermissions,
        permissionHistory=[rootBoxPermissions],
        lastPermissionLayer=rootBoxPermissions,
    )
    return thisBox


def getBoxFromParentChain(db, path, parentBox):
    """ Given a path and a box to start with,
        the box identified by the path is returned,
        with all its permissions set along the way.
    """
    subBoxDict = dbRetrieveRecordByKey(
        db,
        'boxes',
        {'box_name': path[0], 'parent_id': parentBox.box_id},
        dbTablesDesc=dbSchema,
    )
    if subBoxDict is None:
        return None
    else:
        subPath = path[1:]
        subBox = Box(**subBoxDict)
        thisBoxPermissions = list(dbGetBoxRolePermissions(db, subBox.box_id))
        subBox.updatePermissionData(
            fromBox=parentBox,
            lastPermissionLayer=thisBoxPermissions,
        )
        if len(subPath) < 1:
            return subBox
        else:
            return getBoxFromParentChain(db, subPath, subBox)


def getBoxFromPath(db, path, user, accountDeletionInProgress=False):
    """ Given a full path as a list of boxId's (starting with ""),
        the box object is returned if it exists - otherwise None.
        The box object is equipped with permission features:
            - the folded permissions (as inherited along the path)
            - the full permission-set lists accumulated along the path
            - the identity of the native vs inherited permission role ids.

        As anywhere, accountDeletionInProgress=True means that we ignore
        permissions for the sake of reaching, and then erasing/amending,
        all traces of a user who is about to be deleted.
    """
    rootBox = getRootBox(db)
    if len(path) < 1:
        return rootBox
    else:
        childBox = getBoxFromParentChain(
            db,
            path,
            parentBox=rootBox,
        )
        if childBox is not None:
            if (
                accountDeletionInProgress or
                    userHasPermission(db, user, childBox.permissions, 'r')):
                return childBox
            else:
                return None
        else:
            return None


def getFilesFromBox(db, box):
    """ Perform a 'ls' call and return
        all files found in a given box.
    """
    return (
        File(**fileDict)
        for fileDict in dbRetrieveRecordsByKey(
            db,
            'files',
            {'box_id': box.box_id},
            dbTablesDesc=dbSchema,
        )
    )


def getLinksFromBox(db, box):
    """ Perform a 'ls' call and return
        all links found in a given box.
    """
    return (
        Link(**linkDict)
        for linkDict in dbRetrieveRecordsByKey(
            db,
            'links',
            {'box_id': box.box_id},
            dbTablesDesc=dbSchema,
        )
    )


def getFileFromParent(
        db, parentBox, fileName,
        user, accountDeletionInProgress=False):
    """ Given a box and the name of a file supposedly contained
        in it, return the file (or None).
    """
    fileDict = dbRetrieveRecordByKey(
        db,
        'files',
        {'name': fileName, 'box_id': parentBox.box_id},
        dbTablesDesc=dbSchema,
    )
    if fileDict is not None:
        return File(**fileDict)
    else:
        return None


def getLinkFromParent(
        db, parentBox, linkName,
        user, accountDeletionInProgress=False):
    """ Given a box and the name of a link supposedly contained
        in it, return the link (or None).
    """
    linkDict = dbRetrieveRecordByKey(
        db,
        'links',
        {'name': linkName, 'box_id': parentBox.box_id},
        dbTablesDesc=dbSchema,
    )
    if linkDict is not None:
        return Link(**linkDict)
    else:
        return None


def makeBoxInParent(db, parentBox, newBox, user, skipCommit=False):
    """ Create a box, with name newBox, in parentBox
        on behalf of 'user'. Does all permission/name availability checks.
    """
    # first we check user has permission to create boxes here
    if not userHasPermission(db, user, parentBox.permissions, 'c'):
        raise OstracionError('User is not allowed to create boxes')
    else:
        # then we check there are no children with same name in the parent
        if not isNameUnderParentBox(db, parentBox, newBox.box_name):
            # now we create
            dbAddRecordToTable(
                db,
                'boxes',
                newBox.asDict(),
                dbTablesDesc=dbSchema,
            )
            if not skipCommit:
                db.commit()
        else:
            raise OstracionError('Name already exists')


def updateBox(
        db, path, newBox, user,
        accountDeletionInProgress=False, skipCommit=False):
    """ Update the fields of a box on DB."""
    #
    # we check box_id is unchanged for updating
    prevBox = getBoxFromPath(
        db,
        path,
        user,
        accountDeletionInProgress=accountDeletionInProgress,
    )
    parentBox = getBoxFromPath(
        db,
        path[:-1],
        user,
        accountDeletionInProgress=accountDeletionInProgress,
    )
    if newBox.box_id != prevBox.box_id:
        raise RuntimeError('Box ID mismatch')
    else:
        if (
                not accountDeletionInProgress and
                not userHasPermission(db, user, prevBox.permissions, 'w')):
            raise OstracionError('User is not allowed to edit box')
        else:
            if not isNameUnderParentBox(
                    db,
                    parentBox,
                    newBox.box_name,
                    excludedIds=[('box', newBox.box_id)]):
                newBoxItem = Box(**{
                    k: v
                    for k, v in newBox.asDict().items()
                    if k not in {
                        'dvector_box_name',
                        'dvector_title',
                        'dvector_description',
                    }
                })
                dbUpdateRecordOnTable(
                    db,
                    'boxes',
                    newBoxItem.asDict(),
                    dbTablesDesc=dbSchema,
                )
                if not skipCommit:
                    db.commit()
            else:
                raise OstracionError('Name already exists')


def updateFile(
        db, boxPath, prevFileName, newFile, user,
        accountDeletionInProgress=False, skipCommit=False):
    """ Update the fields of a file object on DB."""
    #
    # we check file_id is unchanged
    parentBox = getBoxFromPath(
        db,
        boxPath,
        user,
        accountDeletionInProgress=accountDeletionInProgress,
    )
    prevFile = getFileFromParent(
        db,
        parentBox,
        prevFileName,
        user,
        accountDeletionInProgress=accountDeletionInProgress,
    )
    if newFile.file_id != prevFile.file_id:
        raise RuntimeError('File ID mismatch')
    else:
        if (not accountDeletionInProgress and
                not userHasPermission(db, user, parentBox.permissions, 'w')):
            raise OstracionError('User is not allowed to edit file')
        else:
            if not isNameUnderParentBox(
                    db, parentBox, newFile.name,
                    excludedIds=[('file', prevFile.file_id)]):
                newFileItem = File(**{
                    k: v
                    for k, v in newFile.asDict().items()
                    if k not in {'dvector_name', 'dvector_description'}
                })
                dbUpdateRecordOnTable(
                    db,
                    'files',
                    newFileItem.asDict(),
                    dbTablesDesc=dbSchema,
                )
                if not skipCommit:
                    db.commit()
            else:
                raise OstracionError('Name already exists')


def isNameUnderParentBox(db, parentBox, newName, excludedIds=[]):
    """ Check if the proposed name is already an identifier in the box.
        User-agnostic call, i.e. looks in all contained items for the check.
    """
    return isBoxNameUnderParentBox(
        db=db,
        parentBox=parentBox,
        newName=newName,
        excludedIds=excludedIds,
    ) or isFileNameUnderParentBox(
        db=db,
        parentBox=parentBox,
        newName=newName,
        excludedIds=excludedIds,
    ) or isLinkNameUnderParentBox(
        db=db,
        parentBox=parentBox,
        newName=newName,
        excludedIds=excludedIds,
    )


def isBoxNameUnderParentBox(db, parentBox, newName, excludedIds=[]):
    """ Check if the proposed name is already a contained box.
        User-agnostic: only gives a yes/no answer
        to the question: can I use this as box/file name?
        (hence it needs to know the complete list of contained items).
    """
    exIds = {p[1] for p in excludedIds if p[0] == 'box'}
    return newName in (
        box['box_name']
        for box in dbRetrieveRecordsByKey(
            db,
            'boxes',
            {'parent_id': parentBox.box_id},
            dbTablesDesc=dbSchema,
        )
        if box['box_id'] not in exIds
    )


def isFileNameUnderParentBox(db, parentBox, newName, excludedIds=[]):
    """ Check if the proposed name is already a contained file.
        User-agnostic: only gives a yes/no answer
        to the question: can I use this as box/file name?
        (hence it needs to know the complete list of contained items).
    """
    exIds = {p[1] for p in excludedIds if p[0] == 'file'}
    return newName in (
        file['name']
        for file in dbRetrieveRecordsByKey(
            db,
            'files',
            {'box_id': parentBox.box_id},
            dbTablesDesc=dbSchema,
        )
        if file['file_id'] not in exIds
    )


def isLinkNameUnderParentBox(db, parentBox, newName, excludedIds=[]):
    """ Check if the proposed name is already a contained link.
        User-agnostic: only gives a yes/no answer
        to the question: can I use this as box/file/... name?
        (hence it needs to know the complete list of contained items).
    """
    exIds = {p[1] for p in excludedIds if p[0] == 'link'}
    return newName in (
        link['name']
        for link in dbRetrieveRecordsByKey(
            db,
            'links',
            {'box_id': parentBox.box_id},
            dbTablesDesc=dbSchema,
        )
        if link['link_id'] not in exIds
    )


def isAncestorBoxOf(db, higherBox, childBox):
    """ Return True if higherBox is among the direct ancestors of childBox
        all the way up to root.
        In particular, True if the two arguments are the same box
    """
    def _retrieveAncestorIds(db, bx, ids=[]):
        if bx.box_id == '':
            return ids + [bx.box_id]
        else:
            return _retrieveAncestorIds(
                db,
                Box(**dbRetrieveRecordByKey(
                    db,
                    'boxes',
                    {'box_id': bx.parent_id},
                    dbTablesDesc=dbSchema,
                )),
                ids=ids + [bx.box_id],
            )
    #
    return higherBox.box_id in _retrieveAncestorIds(db, childBox)


def _recursiveBoxDeletion(
        db, box, parentBox, user,
        fileStorageDirectory, accountDeletionInProgress=False):
    """ Take care of deleting a box, invoking itself on children boxes
        and erasing contained files, joining the results (the delete queue)
        accumulated in the sub-deletions. Used internaly by deleteBox.
    """
    if box.box_id == '':
        raise OstracionError('Box cannot be deleted')
    else:
        if (accountDeletionInProgress or
                (
                    userHasPermission(db, user, box.permissions, 'w') and
                    userHasPermission(db, user, parentBox.permissions, 'c')
                )):
            fsDeleteQueue = ([fileIdToPath(
                box.icon_file_id,
                fileStorageDirectory=fileStorageDirectory,
            )]) if box.icon_file_id != '' else []
            allChildren = list(getBoxesFromParent(db, box, user))
            if any(c is None for c in allChildren):
                raise OstracionError('User is not allowed to delete box')
            #
            for c in allChildren:
                if c is not None:
                    fsDeleteQueue += _recursiveBoxDeletion(
                        db, c, box, user,
                        fileStorageDirectory=fileStorageDirectory,
                        accountDeletionInProgress=accountDeletionInProgress)
            allChildFiles = getFilesFromBox(db, box)
            for f in allChildFiles:
                fsDeleteQueue += deleteFile(
                    db, box, f, user,
                    fileStorageDirectory=fileStorageDirectory,
                    skipCommit=True,
                    accountDeletionInProgress=accountDeletionInProgress)
            # actual deletion
            dbDeleteRecordsByKey(
                db, 'box_role_permissions', {'box_id': box.box_id},
                dbTablesDesc=dbSchema)
            dbDeleteRecordsByKey(
                db, 'boxes', {'box_id': box.box_id},
                dbTablesDesc=dbSchema)
            return fsDeleteQueue
        else:
            raise OstracionError('User is not allowed to delete box')


def canDeleteBox(db, box, parentBox, user):
    """ Return whether the user can delete the box,
        i.e. w-permission on the box, c-permission on the parent
        and canDeleteBox on all sub-boxes.
    """
    if box.box_id == '':
        # root cannot be deleted
        return False
    else:
        return all([
            userHasPermission(db, user, box.permissions, 'w'),
            userHasPermission(db, user, parentBox.permissions, 'c')
        ]) and all([
            cBox is not None and canDeleteBox(db, cBox, box, user)
            for cBox in getBoxesFromParent(db, box, user)
        ])


def deleteBox(
        db, box, parentBox, user, fileStorageDirectory,
        accountDeletionInProgress=False, skipCommit=False):
    """ Delete the box and return the deletequeue
        (no actual-FS deletions performed in this function).

        This will work recursively by handling the
        transaction only at the outer level.
    """
    try:
        fsDeleteQueue = _recursiveBoxDeletion(
            db, box, parentBox, user,
            fileStorageDirectory=fileStorageDirectory,
            accountDeletionInProgress=accountDeletionInProgress,
        )
        if not skipCommit:
            db.commit()
        return fsDeleteQueue
    except Exception as e:
        db.rollback()
        raise e


def deleteFile(
        db, parentBox, file, user, fileStorageDirectory,
        skipCommit=False, accountDeletionInProgress=False):
    """ Delete a file (either because permissions allow it
        or the caller is working as part of an account deletion,
        in which case the caller is responsible for lifting
        permission checks).
        Returns the filesystem delete queue.
    """
    if (accountDeletionInProgress or
            userHasPermission(db, user, parentBox.permissions, 'w')):
        #
        fsDeleteQueue = [
            fileIdToPath(
                file.file_id,
                fileStorageDirectory=fileStorageDirectory,
            )
        ]+(
            [
                fileIdToPath(
                    file.icon_file_id,
                    fileStorageDirectory=fileStorageDirectory,
                )
            ]
            if file.icon_file_id != '' else []
        )
        dbDeleteRecordsByKey(
            db,
            'files',
            {'file_id': file.file_id},
            dbTablesDesc=dbSchema,
        )
        if not skipCommit:
            db.commit()
        return fsDeleteQueue
    else:
        raise OstracionError('User has no write permission')


def makeFileInParent(db, parentBox, newFile):
    """ Create a file object in a box."""
    if newFile.box_id != parentBox.box_id:
        raise RuntimeError('wrong parent box id in makeFileInParent')
    else:
        if not isBoxNameUnderParentBox(db, parentBox, newFile.name):
            dbAddRecordToTable(
                db,
                'files',
                newFile.asDict(),
                dbTablesDesc=dbSchema,
            )
            db.commit()
        else:
            raise OstracionError('Name already exists')


def updateLink(
        db, boxPath, prevLinkName, newLink, user,
        accountDeletionInProgress=False, skipCommit=False):
    """ Update the fields of a link object on DB."""
    #
    # we check link_id is unchanged
    parentBox = getBoxFromPath(
        db,
        boxPath,
        user,
        accountDeletionInProgress=accountDeletionInProgress,
    )
    prevLink = getLinkFromParent(
        db,
        parentBox,
        prevLinkName,
        user,
        accountDeletionInProgress=accountDeletionInProgress,
    )
    if newLink.link_id != prevLink.link_id:
        raise RuntimeError('Link ID mismatch')
    else:
        if (not accountDeletionInProgress and
                not userHasPermission(db, user, parentBox.permissions, 'w')):
            raise OstracionError('User is not allowed to edit link')
        else:
            if not isNameUnderParentBox(
                    db, parentBox, newLink.name,
                    excludedIds=[('link', prevLink.link_id)]):
                newLinkItem = Link(**{
                    k: v
                    for k, v in newLink.asDict().items()
                    if k not in {
                        'dvector_name',
                        'dvector_description',
                        'dvector_title',
                    }
                })
                dbUpdateRecordOnTable(
                    db,
                    'links',
                    newLinkItem.asDict(),
                    dbTablesDesc=dbSchema,
                )
                if not skipCommit:
                    db.commit()
            else:
                raise OstracionError('Name already exists')


def deleteLink(
        db, parentBox, link, user, fileStorageDirectory,
        skipCommit=False, accountDeletionInProgress=False):
    """ Delete a link (either because permissions allow it
        or the caller is working as part of an account deletion,
        in which case the caller is responsible for lifting
        permission checks).
        Returns the filesystem delete queue.
    """
    if (accountDeletionInProgress or
            userHasPermission(db, user, parentBox.permissions, 'w')):
        #
        fsDeleteQueue = (
            [
                fileIdToPath(
                    link.icon_file_id,
                    fileStorageDirectory=fileStorageDirectory,
                )
            ]
            if link.icon_file_id != '' else []
        )
        dbDeleteRecordsByKey(
            db,
            'links',
            {'link_id': link.link_id},
            dbTablesDesc=dbSchema,
        )
        if not skipCommit:
            db.commit()
        return fsDeleteQueue
    else:
        raise OstracionError('User has no write permission')


def makeLinkInParent(
        db, user, parentBox, date, linkName, linkTitle, linkDescription,
        linkTarget, linkOptions={}):
    """ Create a new external link object in the specified box.

        Return a dummy value (True upon success, but it is the errors
        that are raised.)
    """
    if userHasPermission(db, user, parentBox.permissions, 'w'):
        if not isNameUnderParentBox(db, parentBox, linkName):
            userName = user.username if user.is_authenticated else ''
            newLink = Link(
                box_id=parentBox.box_id,
                name=linkName,
                title=linkTitle,
                description=linkDescription,
                icon_file_id='',
                date=date,
                creator_username=userName,
                icon_file_id_username=userName,
                icon_mime_type='',
                metadata_username=userName,
                target=linkTarget,
                metadata_dict=linkOptions,
            )
            dbAddRecordToTable(
                db,
                'links',
                newLink.asDict(),
                dbTablesDesc=dbSchema,
            )
            db.commit()
        else:
            raise OstracionError('Name already exists')
    else:
        raise OstracionError('User has no write permission')


def updateLinkThumbnail(
        db, link, tId, tMT, user, fileStorageDirectory,
        accountDeletionInProgress=False, skipCommit=False):
    """ Update the thumbnail info for a link.
        Return a list of zero or one full paths for deletion."""
    prevId = link.icon_file_id
    if prevId != '':
        delQueue = [fileIdToPath(
            prevId,
            fileStorageDirectory=fileStorageDirectory,
        )]
    else:
        delQueue = []
    #
    link.icon_file_id = tId if tId is not None else ''
    link.icon_mime_type = tMT if tMT is not None else ''
    link.icon_file_id_username = (
        user.username if user.is_authenticated else ''
    ) if not accountDeletionInProgress else ''
    dbUpdateRecordOnTable(
        db,
        'links',
        link.asDict(),
        dbTablesDesc=dbSchema,
    )
    #
    if not skipCommit:
        db.commit()
    return delQueue


def updateFileThumbnail(
        db, file, tId, tMT, user, fileStorageDirectory,
        accountDeletionInProgress=False, skipCommit=False):
    """ Update the thumbnail info for a file.
        Return a list of zero or one full paths for deletion."""
    prevId = file.icon_file_id
    if prevId != '':
        delQueue = [fileIdToPath(
            prevId,
            fileStorageDirectory=fileStorageDirectory,
        )]
    else:
        delQueue = []
    #
    file.icon_file_id = tId if tId is not None else ''
    file.icon_mime_type = tMT if tMT is not None else ''
    file.icon_file_id_username = (
        user.username if user.is_authenticated else ''
    ) if not accountDeletionInProgress else ''
    dbUpdateRecordOnTable(
        db,
        'files',
        file.asDict(),
        dbTablesDesc=dbSchema,
    )
    #
    if not skipCommit:
        db.commit()
    return delQueue


def updateUserThumbnail(
        db, targetUser, tId, tMT, user,
        fileStorageDirectory, skipCommit=False):
    """ Update the thumbnail info for a user.
        Return a list of zero or one full paths for deletion."""
    prevId = targetUser.icon_file_id
    if prevId != '':
        delQueue = [
            fileIdToPath(prevId, fileStorageDirectory=fileStorageDirectory)
        ]
    else:
        delQueue = []
    #
    targetUser.icon_file_id = tId if tId is not None else ''
    targetUser.icon_mime_type = tMT if tMT is not None else ''
    targetUser.icon_file_id_username = (
        user.username
    ) if user.is_authenticated else ''
    dbUpdateRecordOnTable(
        db,
        'users',
        targetUser.asDict(),
        dbTablesDesc=dbSchema,
    )
    #
    if not skipCommit:
        db.commit()
    return delQueue


def updateBoxThumbnail(
        db, box, tId, tMT, user, fileStorageDirectory,
        accountDeletionInProgress=False, skipCommit=False):
    """ Update the thumbnail info for a box.
        Return a list of zero or one full paths for deletion."""
    prevId = box.icon_file_id
    if prevId != '':
        delQueue = [
            fileIdToPath(prevId, fileStorageDirectory=fileStorageDirectory)
        ]
    else:
        delQueue = []
    #
    box.icon_file_id = tId if tId is not None else ''
    box.icon_mime_type = tMT if tMT is not None else ''
    box.icon_file_id_username = (
        user.username if user.is_authenticated else ''
    ) if not accountDeletionInProgress else ''
    dbUpdateRecordOnTable(
        db,
        'boxes',
        box.asDict(),
        dbTablesDesc=dbSchema,
    )
    #
    if not skipCommit:
        db.commit()
    return delQueue


def moveFile(
        db, file, srcBox, dstBox, user,
        fileStorageDirectory, skipCommit=False):
    """ Move a file between boxes: also
        check for w permission on both boxes,
        check that no box in dstBox yields a name clash."""
    if file.box_id != srcBox.box_id:
        raise OstracionError('Parent mismatch between file and source box')
    elif srcBox.box_id == dstBox.box_id:
        raise OstracionError('Source and destination are the same')
    else:
        if all([
            userHasPermission(db, user, srcBox.permissions, 'w'),
            userHasPermission(db, user, dstBox.permissions, 'w'),
        ]):
            #
            fileName = file.name
            if isNameUnderParentBox(db, dstBox, linkName):
                raise OstracionError(
                    'Destination box contains an item with same name'
                )
            else:
                # now can the actual MV be performed
                newFile = recursivelyMergeDictionaries(
                    {'box_id': dstBox.box_id},
                    defaultMap=file.asDict(),
                )
                dbUpdateRecordOnTable(
                    db,
                    'files',
                    newFile,
                    dbTablesDesc=dbSchema,
                )
                #
                if not skipCommit:
                    db.commit()
                #
                messages = []
                return messages
        else:
            raise OstracionError('User has no write permission')


def moveBox(db, box, srcBox, dstBox, user, skipCommit=False):
    """ Move 'box' from being contained in
        'srcBox' to being contained in 'dstBox'
        (with all involved permission checks).
    """
    if box.box_id == '':
        # nobody can touch root
        raise OstracionError('Cannot act on this object')
    else:
        if box.parent_id != srcBox.box_id:
            # consistency in request
            raise RuntimeError(
                'Parent mismatch between box to move and source box'
            )
        else:
            if box.parent_id == dstBox.box_id:
                raise OstracionError(
                    'Source and destination box are the same'
                )
            else:
                if not canDeleteBox(db, box, srcBox, user):
                    # must be able to remove from source
                    raise OstracionError(
                        'Insufficient permissions to move box away'
                    )
                else:
                    if not all(
                            userHasPermission(
                                db, user, dstBox.permissions, prm
                            )
                            for prm in {'w', 'c'}):
                        # must be able to upload and create to dest
                        raise OstracionError(
                            'Insufficient permissions to move boxes '
                            'to the destination box'
                        )
                    else:
                        # name clash check for destination
                        if isNameUnderParentBox(db, dstBox, box.box_name):
                            raise OstracionError(
                                'An object with that name '
                                'exists already'
                            )
                        else:
                            # check against box incest
                            if isAncestorBoxOf(db, box, dstBox):
                                raise OstracionError(
                                    'Cannot move box to a sub-box of itself'
                                )
                            else:
                                # perform the move
                                newBox = recursivelyMergeDictionaries(
                                    {'parent_id': dstBox.box_id},
                                    defaultMap=box.asDict(),
                                )
                                dbUpdateRecordOnTable(
                                    db,
                                    'boxes',
                                    newBox,
                                    dbTablesDesc=dbSchema,
                                )
                                #
                                if not skipCommit:
                                    db.commit()
                                return []


def moveLink(
        db, link, srcBox, dstBox, user,
        fileStorageDirectory, skipCommit=False):
    """ Move a link between boxes: also
        check for w permission on both boxes,
        check that no item in dstBox yields a name clash."""
    if link.box_id != srcBox.box_id:
        raise OstracionError('Parent mismatch between link and source box')
    elif srcBox.box_id == dstBox.box_id:
        raise OstracionError('Source and destination are the same')
    else:
        if all([
            userHasPermission(db, user, srcBox.permissions, 'w'),
            userHasPermission(db, user, dstBox.permissions, 'w'),
        ]):
            #
            linkName = link.name
            if isNameUnderParentBox(db, dstBox, linkName):
                raise OstracionError(
                    'Destination box contains an item with same name'
                )
            else:
                # now can the actual MV be performed
                newLink = recursivelyMergeDictionaries(
                    {'box_id': dstBox.box_id},
                    defaultMap=link.asDict(),
                )
                dbUpdateRecordOnTable(
                    db,
                    'links',
                    newLink,
                    dbTablesDesc=dbSchema,
                )
                #
                if not skipCommit:
                    db.commit()
                #
                messages = []
                return messages
        else:
            raise OstracionError('User has no write permission')
