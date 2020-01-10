""" userTools.py
    Tools to work with users on the database.
"""

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries
)

from ostracion_app.utilities.models.Box import Box
from ostracion_app.utilities.models.File import File
from ostracion_app.utilities.models.Link import Link
from ostracion_app.utilities.models.User import User
from ostracion_app.utilities.models.UserRole import UserRole

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.database.sqliteEngine import (
    dbRetrieveAllRecords,
    dbAddRecordToTable,
    dbRetrieveRecordByKey,
    dbUpdateRecordOnTable,
    dbDeleteRecordsByKey,
)
from ostracion_app.utilities.database.dbSchema import (
    dbSchema,
)

from ostracion_app.utilities.database.permissions import (
    userIsAdmin,
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
    isNameUnderParentBox,
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

from ostracion_app.utilities.database.settingsTools import (
    dbGetSetting,
)


def dbGetUser(db, username):
    """Retrieve a user given its username."""
    userDict = dbRetrieveRecordByKey(
        db,
        'users',
        {'username': username},
        dbTablesDesc=dbSchema,
    )
    return User(**userDict) if userDict is not None else None


def dbGetAllUsers(db, user):
    """Get a listing of all existing users (except the '' system user)."""
    if userIsAdmin(db, user):
        return (
            User(**u)
            for u in dbRetrieveAllRecords(
                db,
                'users',
                dbTablesDesc=dbSchema,
            )
            if u['username'] != ''
        )
    else:
        raise OstracionError('Insufficient permissions')


def getUserFullName(db, username):
    """Resolve a username to the current full name."""
    fUser = dbGetUser(db, username)
    if fUser is None:
        return '(no user)'
    else:
        return fUser.fullname


def dbUpdateUser(db, newUser, user, skipCommit=False):
    """Update some columns of a user row."""
    if newUser.username != '':
        dbUpdateRecordOnTable(
            db,
            'users',
            newUser.asDict(),
            dbTablesDesc=dbSchema,
        )
        if not skipCommit:
            db.commit()
    else:
        raise OstracionError('Cannot alter system user')


def dbCreateUser(db, newUser, user):
    """Create a new user row."""
    dbAddRecordToTable(
        db,
        'users',
        newUser.asDict(),
        dbTablesDesc=dbSchema,
    )
    # we read the config flag about new users having or not the 'ticketer' role
    # new_users_are_ticketer
    addTicketerRole = dbGetSetting(
        db,
        'behaviour',
        'behaviour_tickets',
        'new_users_are_ticketer',
        user
    )['value']
    if addTicketerRole:
        dbAddRecordToTable(
            db,
            'user_roles',
            UserRole(username=newUser.username, role_id='ticketer').asDict(),
            dbTablesDesc=dbSchema,
        )
    #
    db.commit()


def _findFirstAvailableDeletedObjectName(db, parentBox, prefix):
    """ Build a file/box name without name conflicts in a box.
        Used upon account deletions for cases of forced renames.
    """
    tryIndex = 1
    while isNameUnderParentBox(db, parentBox, '%s%i' % (prefix, tryIndex)):
        tryIndex += 1
    return '%s%i' % (prefix, tryIndex)


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
                newFileName = _findFirstAvailableDeletedObjectName(
                    db,
                    parentBox,
                    prefix='REDACTED_FILE_'
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
                newLinkName = _findFirstAvailableDeletedObjectName(
                    db,
                    parentBox,
                    prefix='REDACTED_LINK_'
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
                    newBoxName = _findFirstAvailableDeletedObjectName(
                        db,
                        parentBox,
                        prefix='REDACTED_BOX_',
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


def dbDeleteUser(db, username, user, fileStorageDirectory):
    """ Delete a user altogether. Return a fsDeletionQueue for deletions."""
    if username != '':
        if not userIsAdmin(db, dbGetUser(db, username)):
            try:
                if username == user.username or userIsAdmin(db, user):
                    fsDeleteQueue = []
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
                    for u in dbGetAllUsers(db, user):
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
                    # 3. finally, delete the user
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
