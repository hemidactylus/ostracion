"""
    userDeletion.py
        Tools to handle the complex operation of deleting a user.
        This is separated from 'userTools' since it involves higher-level
        handling and is tied to registered apps with their hooks
        and it would cause circular references otherwise.
"""

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries
)
from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.models.Box import Box
from ostracion_app.utilities.models.File import File
from ostracion_app.utilities.models.Link import Link
from ostracion_app.utilities.models.User import User
from ostracion_app.utilities.database.sqliteEngine import (
    dbDeleteRecordsByKey,
)
from ostracion_app.utilities.database.dbSchema import (
    dbSchema,
)
from ostracion_app.utilities.database.permissions import (
    userIsAdmin,
)
from ostracion_app.utilities.database.userTools import (
    dbGetUser,
    dbGetAllUsers,
    dbUpdateUser,
)

from ostracion_app.utilities.database.fileSystem import (
    getRootBox,
    getBoxesFromParent,
    getFilesFromBox,
    deleteFile,
    getLinksFromBox,
    deleteLink,
    updateFileThumbnail,
    updateBoxThumbnail,
    updateLinkThumbnail,
    findFirstAvailableObjectNameInBox,
    deleteBox,
    getFileFromParent,
    getLinkFromParent,
    updateBox,
    updateFile,
    updateLink,
    getBoxFromPath,
)
from ostracion_app.utilities.fileIO.physical import (
    fileIdToPath,
)
from ostracion_app.views.apps.appUserDeletionHooks import (
    userDeletionHookMap,
)


def _traverseForAccountDeletion(db, parentBox, username, user,
                                path, fileStorageDirectory):
    """ Traverse the tree (one call per box, recursively+iteratively)
        and collect a delete queue while updating items found in various
        ways (deletions, icon resets, metadata resets, forced renames).
    """
    fsDeleteQueue = []
    for file in getFilesFromBox(db, parentBox):
        if (file.creator_username == username or
                file.editor_username == username):
            fsDeleteQueue += deleteFile(
                db,
                parentBox,
                file,
                None,
                fileStorageDirectory=fileStorageDirectory,
                skipCommit=True,
                accountDeletionInProgress=True,
            )
        else:
            if file.icon_file_id_username == username:
                fsDeleteQueue += updateFileThumbnail(
                    db,
                    file,
                    None,
                    None,
                    user,
                    fileStorageDirectory=fileStorageDirectory,
                    accountDeletionInProgress=True,
                    skipCommit=True,
                )
                iconedFile = getFileFromParent(db, parentBox, file.name, None)
            else:
                iconedFile = file
            # "iconed" as in "icon-wise fixed"
            if iconedFile.metadata_username == username:
                newFileName = findFirstAvailableObjectNameInBox(
                    db,
                    parentBox,
                    prefix='REDACTED_FILE_',
                    suffix='',
                )
                newDescription = 'File name redacted upon account deletion'
                newFile = File(**recursivelyMergeDictionaries(
                    {
                        'name': newFileName,
                        'description': newDescription,
                        'metadata_username': '',
                    },
                    defaultMap=iconedFile.asDict(),
                ))
                updateFile(
                    db,
                    path,
                    iconedFile.name,
                    newFile,
                    None,
                    accountDeletionInProgress=True,
                    skipCommit=True,
                )
    #
    for link in getLinksFromBox(db, parentBox):
        if link.creator_username == username:
            fsDeleteQueue += deleteLink(
                db,
                parentBox,
                link,
                None,
                fileStorageDirectory=fileStorageDirectory,
                skipCommit=True,
                accountDeletionInProgress=True,
            )
        else:
            if link.icon_file_id_username == username:
                fsDeleteQueue += updateLinkThumbnail(
                    db,
                    link,
                    None,
                    None,
                    user,
                    fileStorageDirectory=fileStorageDirectory,
                    accountDeletionInProgress=True,
                    skipCommit=True,
                )
                iconedLink = getLinkFromParent(db, parentBox, link.name, None)
            else:
                iconedLink = link
            # "iconed" as in "icon-wise fixed"
            if iconedLink.metadata_username == username:
                newLinkName = findFirstAvailableObjectNameInBox(
                    db,
                    parentBox,
                    prefix='REDACTED_LINK_',
                    suffix='',
                )
                newDescription = 'Link data redacted upon account deletion'
                newLink = Link(**recursivelyMergeDictionaries(
                    {
                        'name': newLinkName,
                        'description': newDescription,
                        'target': '#',
                        'metadata_username': '',
                    },
                    defaultMap=iconedLink.asDict(),
                ))
                updateLink(
                    db,
                    path,
                    iconedLink.name,
                    newLink,
                    None,
                    accountDeletionInProgress=True,
                    skipCommit=True,
                )
    #
    for box in getBoxesFromParent(
            db, parentBox, None, accountDeletionInProgress=True):
        if box is not None and box.box_name != '':
            fsDeleteQueue += _traverseForAccountDeletion(
                db,
                box,
                username,
                user,
                path + [box.box_name],
                fileStorageDirectory=fileStorageDirectory,
            )
            if box.creator_username == username and _boxHasNoChildren(db, box):
                fsDeleteQueue += deleteBox(
                    db,
                    box,
                    parentBox,
                    None,
                    fileStorageDirectory=fileStorageDirectory,
                    accountDeletionInProgress=True,
                    skipCommit=True,
                )
            else:
                if (box.icon_file_id_username == username or
                        box.creator_username == username):
                    fsDeleteQueue += updateBoxThumbnail(
                        db,
                        box,
                        None,
                        None,
                        user,
                        fileStorageDirectory=fileStorageDirectory,
                        accountDeletionInProgress=True,
                        skipCommit=True,
                    )
                    iconedBox = getBoxFromPath(
                        db,
                        path + [box.box_name],
                        None,
                        accountDeletionInProgress=True,
                    )
                else:
                    iconedBox = box
                #
                if (iconedBox.metadata_username == username or
                        iconedBox.creator_username == username):
                    #
                    newBoxName = findFirstAvailableObjectNameInBox(
                        db,
                        parentBox,
                        prefix='REDACTED_BOX_',
                        suffix='',
                    )
                    newDescription = 'Box name redacted upon account deletion'
                    mdNewBoxContrib = {
                            'box_name': newBoxName,
                            'description': newDescription,
                            'title': newBoxName,
                            'metadata_username': '',
                    }
                    #
                    if iconedBox.creator_username == username:
                        cNewBoxContrib = {
                            'creator_username': '',
                        }
                    else:
                        cNewBoxContrib = {}
                    #
                    newBox = Box(**recursivelyMergeDictionaries(
                        recursivelyMergeDictionaries(
                            mdNewBoxContrib,
                            defaultMap=cNewBoxContrib,
                        ),
                        defaultMap=iconedBox.asDict(),
                    ))
                    updateBox(
                        db,
                        path + [box.box_name],
                        newBox,
                        None,
                        accountDeletionInProgress=True,
                        skipCommit=True,
                    )
    #
    return fsDeleteQueue


def _boxHasNoChildren(db, box):
    """ Is it true that this box has no children?
        (regardless of visibility-to-this-user issues).
    """
    return (len(list(getFilesFromBox(db, box))) == 0 and
            len(list(
                getBoxesFromParent(
                    db,
                    box,
                    None,
                    accountDeletionInProgress=True
                )
            )) == 0)


def dbDeleteUser(db, username, user, fileStorageDirectory):
    """ Delete a user altogether. Return a fsDeletionQueue for deletions."""
    if username != '':
        if not userIsAdmin(db, dbGetUser(db, username)):
            try:
                if username == user.username or userIsAdmin(db, user):
                    fsDeleteQueue = []
                    # 0. app-related cleanup for user deletion
                    for appId, deletor in userDeletionHookMap.items():
                        fsDeleteQueue += deletor(
                            db,
                            username,
                            user,
                            fileStorageDirectory=fileStorageDirectory,
                        )
                    # 1. cleanup of file system
                    rootBox = getRootBox(db)
                    fsDeleteQueue += _traverseForAccountDeletion(
                        db,
                        rootBox,
                        username,
                        user,
                        path=[''],
                        fileStorageDirectory=fileStorageDirectory,
                    )
                    # 2. deleting user-related data around
                    dbDeleteRecordsByKey(
                        db,
                        'user_roles',
                        {'username': username},
                        dbTablesDesc=dbSchema,
                    )
                    deleteeUser = dbGetUser(db, username)
                    if deleteeUser.icon_file_id != '':
                        fsDeleteQueue.append(fileIdToPath(
                            deleteeUser.icon_file_id,
                            fileStorageDirectory=fileStorageDirectory,
                        ))
                    dbDeleteRecordsByKey(
                        db,
                        'tickets',
                        {'username': username},
                        dbTablesDesc=dbSchema,
                    )
                    for u in dbGetAllUsers(db, user,
                                           accountDeletionInProgress=True):
                        if u.username != username:
                            if u.icon_file_id_username == username:
                                if u.icon_file_id != '':
                                    fsDeleteQueue.append(fileIdToPath(
                                        u.icon_file_id,
                                        fileStorageDirectory,
                                    ))
                                dbUpdateUser(
                                    db,
                                    User(**recursivelyMergeDictionaries(
                                        {
                                            'icon_file_id': '',
                                            'icon_file_id_username': '',
                                        },
                                        defaultMap=u.asDict(),
                                    )),
                                    user,
                                    skipCommit=True,
                                )
                    # 3. delete user-specific role association from boxes
                    dbDeleteRecordsByKey(
                        db,
                        'box_role_permissions',
                        {'role_class': 'user', 'role_id': username},
                        dbTablesDesc=dbSchema,
                    )
                    # 4. delete user-specific role
                    dbDeleteRecordsByKey(
                        db,
                        'roles',
                        {'role_class': 'user', 'role_id': username},
                        dbTablesDesc=dbSchema
                    )
                    # 5. finally, delete the user
                    dbDeleteRecordsByKey(
                        db,
                        'users',
                        {'username': username},
                        dbTablesDesc=dbSchema
                    )
                    db.commit()
                    return fsDeleteQueue
                else:
                    raise OstracionError('Insufficient permissions')
            except Exception as e:
                db.rollback()
                raise e
        else:
            raise OstracionError('Cannot delete an admin')
    else:
        raise OstracionError('Cannot alter system user')
