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
from ostracion_app.utilities.models.Role import Role
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


def dbGetAllUsers(db, user, accountDeletionInProgress=False):
    """Get a listing of all existing users (except the '' system user)."""
    if accountDeletionInProgress or userIsAdmin(db, user):
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
            UserRole(
                username=newUser.username,
                role_class='system',
                role_id='ticketer',
            ).asDict(),
            dbTablesDesc=dbSchema,
        )
    # user-tied role handling
    dbAddRecordToTable(
        db,
        'roles',
        Role(
            role_id=newUser.username,
            description='%s user-role' % newUser.username,
            role_class='user',
            can_box=1,
            can_user=0,
            can_delete=0,
        ).asDict(),
        dbTablesDesc=dbSchema,
    )
    dbAddRecordToTable(
        db,
        'user_roles',
        UserRole(
            username=newUser.username,
            role_class='user',
            role_id=newUser.username,
        ).asDict(),
        dbTablesDesc=dbSchema,
    )
    #
    db.commit()
