""" permissions.py

    DB tools to operate on permisions
    (roles and their user- and box- associations
    for a healthy navigation/operation on items).
"""

from functools import wraps

from flask import (
    g,
    abort,
)

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries,
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.models.User import User
from ostracion_app.utilities.models.BoxRolePermission import BoxRolePermission
from ostracion_app.utilities.models.Role import Role
from ostracion_app.utilities.models.UserRole import UserRole

from ostracion_app.utilities.database.sqliteEngine import (
    dbRetrieveAllRecords,
    dbRetrieveRecordByKey,
    dbRetrieveRecordsByKey,
    dbAddRecordToTable,
    dbDeleteRecordsByKey,
    dbUpdateRecordOnTable,
)

from ostracion_app.utilities.database.dbSchema import (
    dbSchema,
)

from ostracion_app.utilities.tools.listTools import (
    orderPreservingUniquifyList,
)


# Decorator for endpoint functions
def userRoleRequired(roleKeys):
    """ Generate a decorator for an endpoint function
        that blocks users who do not have at least
        one of the provided roles (by ID).
    """
    def epDecorator(epf):
        # this tweaks the name '_decorated' so to avoid name clash
        # that otherwise Flask would raise (same name for different endpoints)
        @wraps(epf)
        def _decorated(*pargs, **kwargs):
            user = g.user
            if (user.is_authenticated and
                    len(set(roleKeys) & {r.roleKey() for r in user.roles}) > 0):
                return epf(*pargs, **kwargs)
            else:
                return abort(
                    400,
                    'User has no permission to access this resource.',
                )
        return _decorated
    return epDecorator


def _roleSetSorter(rSet):
    """ Make a role set (whose elements are
        2-tuples (role_class, role_id)
        into a sortable item
        for all various no-redundancy operations
        in the permission algebra.
    """
    return (
        len(rSet),
        ' '.join('%s/%s' % _r for _r in sorted(rSet)),
    )


def generalisedGetUserRoles(db, user):
    """ Look up the roles of the user
        taking into account the non-logged-in case.
    """
    if user is not None:
        if hasattr(user, 'roles') and user.roles is not None:
            return user.roles
        else:
            # the user object can have been created e.g.
            # during an user deletion request and not via the login
            # flask handler (whereupon it would get roles as well)
            return list(dbGetUserRoles(db, user))            
    else:
        return [
            Role(**dbRetrieveRecordByKey(
                    db,
                    'roles',
                    {'role_class': 'system', 'role_id': 'anonymous'},
                    dbTablesDesc=dbSchema,
                )
            )
        ]


def userHasRole(db, user, roleClass, roleId):
    """Check if a user has a given role."""
    userRoles = generalisedGetUserRoles(db, user)
    return (userRoles is not None and
            any(r.roleKey() == (roleClass, roleId) for r in userRoles))


def userIsAdmin(db, user):
    """ Check if the given user is admin
        (i.e. belongs to the 'admin' role).
    """
    return userHasRole(db, user, 'system', 'admin')


def isUserWithinPermissionCircle(db, user, circleId):
    """ Check if user is in one of the hard-written perission circles.
        CircleId can be (lowercase):
            anybody
            admins
            nobody
    """
    if circleId == 'nobody':
        return False
    elif circleId == 'anybody':
        return True
    elif circleId == 'admins':
        return userIsAdmin(db, user)


def dbDeleteRole(db, roleClass, roleId, user):
    """ Delete a role from DB."""
    if userIsAdmin(db, user):
        role = dbGetRole(db, roleClass, roleId, user)
        if role.can_delete == 0:
            raise OstracionError('Role cannot be deleted')
        else:
            dbDeleteRecordsByKey(
                db,
                'box_role_permissions',
                {'role_class': role.role_class, 'role_id': role.role_id},
                dbTablesDesc=dbSchema,
            )
            dbDeleteRecordsByKey(
                db,
                'roles',
                {'role_class': role.role_class, 'role_id': role.role_id},
                dbTablesDesc=dbSchema,
            )
            db.commit()
    else:
        raise OstracionError('Insufficient permissions')


def dbCreateRole(db, newRole, user):
    """Create a new role in DB."""
    if userIsAdmin(db, user):
        if dbGetRole(db, newRole.role_class, newRole.role_id, user) is None:
            if newRole.can_delete == 0:
                raise OstracionError('Manual roles must be deletable')
            else:
                dbAddRecordToTable(
                    db,
                    'roles',
                    newRole.asDict(),
                    dbTablesDesc=dbSchema,
                )
                db.commit()
        else:
            raise OstracionWarning(
                'Role "%s/%s" exists already' % newRole.roleKey()
            )
    else:
        raise OstracionError('Insufficient permissions')


def dbUpdateRole(db, newRole, user):
    """Update role metadata on DB."""
    if userIsAdmin(db, user):
        dbUpdateRecordOnTable(
            db,
            'roles',
            {
                k: v
                for k, v in newRole.asDict().items()
                if k in {'description', 'role_class', 'role_id'}
            },
            dbTablesDesc=dbSchema,
            allowPartial=True,
        )
        db.commit()
    else:
        raise OstracionError('Insufficient permissions')


def dbGetRole(db, roleClass, roleId, user):
    """Retrieve a role from DB by ID."""
    if userIsAdmin(db, user):
        roleDict = dbRetrieveRecordByKey(
            db,
            'roles',
            {'role_id': roleId, 'role_class': roleClass},
            dbTablesDesc=dbSchema,
        )
        if roleDict is not None:
            return Role(**roleDict)
        else:
            return None
    else:
        return None


def dbRevokeRoleFromUser(db, role, targetUser, user):
    """Revoke a role from a user, i.e. ungrant it."""
    if userIsAdmin(db, user):
        grantedRoleKeys = {r.roleKey() for r in targetUser.roles}
        if role.roleKey() not in grantedRoleKeys:
            raise OstracionError('Role is not granted to user')
        else:
            # delicate checks: cannot remove 'admin' from self
            if (user.username == targetUser.username and
                    role.roleKey() == ('system', 'admin')):
                raise OstracionError('Cannot revoke "admin" role from self')
            else:
                dbDeleteRecordsByKey(
                    db,
                    'user_roles',
                    {
                        'username': targetUser.username,
                        'role_class': role.role_class,
                        'role_id': role.role_id,
                    },
                    dbTablesDesc=dbSchema,
                )
                db.commit()
    else:
        raise OstracionError('Insufficient permissions')


def dbGrantRoleToUser(db, role, targetUser, user):
    """Assign a role to a user, i.e. grant it."""
    if userIsAdmin(db, user):
        grantedRoleKeys = {r.roleKey() for r in targetUser.roles}
        if role.can_user == 0:
            raise OstracionError('Role cannot be granted to users')
        elif role.roleKey() in grantedRoleKeys:
            raise OstracionError('Role is already granted to user')
        else:
            #
            newUserRole = UserRole(
                username=targetUser.username,
                role_class=role.role_class,
                role_id=role.role_id,
            )
            dbAddRecordToTable(
                db,
                'user_roles',
                newUserRole.asDict(),
                dbTablesDesc=dbSchema,
            )
            #
            db.commit()
    else:
        raise OstracionError('Insufficient permissions')


def dbGetUserRoles(db, user, asDict=False):
    """ Retrieve roles associated to a user.

        Here we implement the automatic attribution of
        anonymous role to unauthenticated visitors.
    """
    anonymousRole = dbRetrieveRecordByKey(
        db,
        'roles',
        {'role_id': 'anonymous', 'role_class': 'system'},
        dbTablesDesc=dbSchema,
    )
    #
    if user.is_authenticated:
        for userRole in (
            ur
            for urBlock in (
                dbRetrieveRecordsByKey(
                    db,
                    'user_roles',
                    {'username': user.username},
                    dbTablesDesc=dbSchema,
                ),
                (anonymousRole,)
            )
            for ur in urBlock
        ):
            #
            role = dbRetrieveRecordByKey(
                db,
                'roles',
                {
                    'role_class': userRole['role_class'],
                    'role_id': userRole['role_id'],
                },
                dbTablesDesc=dbSchema,
            )
            #
            if asDict:
                yield role
            else:
                yield Role(**role)
    else:
        if asDict:
            yield anonymousRole
        else:
            yield anonymousRole(**role)


def dbGetUsersByRole(db, roleClass, roleId, user):
    """ Get all users with a given roleId attached.

        In particular, a list of "UserRole" instances is
        returned, whose userid is to be inspected.
    """
    if userIsAdmin(db, user):
        return (
            UserRole(**u)
            for u in dbRetrieveRecordsByKey(
                db,
                'user_roles',
                {'role_id': roleId, 'role_class': roleClass},
                dbTablesDesc=dbSchema,
            )
        )
    else:
        raise OstracionError('Insufficient permissions')


def dbGetBoxRolePermissions(db, boxId, asDict=False):
    """ Get all permission sets (i.e. each is <--> a role) for a given box."""
    for brPermission in dbRetrieveRecordsByKey(
        db,
        'box_role_permissions',
        {'box_id': boxId},
        dbTablesDesc=dbSchema,
    ):
        if asDict:
            yield brPermission
        else:
            yield BoxRolePermission(**brPermission)


def dbInsertBoxRolePermission(db, newBoxRolePermission,
                              user, skipCommit=False):
    """Add a new permission-set (i.e. tied to a role) to a box."""
    if newBoxRolePermission.box_id == '':
        raise OstracionError('Cannot add a permission to root box')
    else:
        # system/admin cannot be added/removed
        if newBoxRolePermission.roleKey() == ('system', 'admin'):
            raise OstracionError('Cannot add permissions for admin role')
        else:
            role = dbGetRole(
                db,
                newBoxRolePermission.role_class,
                newBoxRolePermission.role_id,
                user,
            )
            if role is not None:
                # the role must have can_box attribute
                if role.can_box == 0:
                    raise OstracionError(
                        'Cannot add permissions for this role'
                    )
                else:
                    if userIsAdmin(db, user):
                        try:
                            dbAddRecordToTable(
                                db,
                                'box_role_permissions',
                                newBoxRolePermission.asDict(),
                                dbTablesDesc=dbSchema,
                            )
                            if not skipCommit:
                                db.commit()
                        except Exception as e:
                            db.rollback()
                            raise e
                    else:
                        raise OstracionError('Insufficient permissions')
            else:
                raise OstracionError('Could not find role')


def dbDeleteBoxRolePermission(db, boxId, roleClass,
                              roleId, user, skipCommit=False):
    """Remove a permission set (i.e. for a role) from a box."""
    if boxId == '':
        raise OstracionError('Cannot delete root box permissions')
    else:
        if userIsAdmin(db, user):
            recordExists = len(list(
                dbRetrieveRecordsByKey(
                    db,
                    'box_role_permissions',
                    {
                        'box_id': boxId,
                        'role_class': roleClass,
                        'role_id': roleId,
                    },
                    dbTablesDesc=dbSchema,
                )
            )) != 0
            if recordExists:
                try:
                    dbDeleteRecordsByKey(
                        db,
                        'box_role_permissions',
                        {
                            'box_id': boxId,
                            'role_class': roleClass,
                            'role_id': roleId,
                        },
                        dbTablesDesc=dbSchema,
                    )
                    if not skipCommit:
                        db.commit()
                except Exception as e:
                    db.rollback()
                    raise e
            else:
                raise OstracionError('Box role permission does not exist')
        else:
            raise OstracionError('Insufficient permissions')


def dbToggleBoxRolePermissionBit(db, thisBox, roleClass, roleId,
                                 bit, user, skipCommit=False):
    """ Toggle (t<-->f) a bit from an existing
        permission set (a role) for a box.
    """
    roleKey = (roleClass, roleId)
    if thisBox.box_id == '' and roleKey == ('system', 'admin'):
        raise OstracionError('Cannot edit root box permissions for admin')
    elif thisBox.box_id == '' and roleKey == ('system', 'anonymous'):
        raise OstracionError('Cannot edit root box permissions for anonymous')
    else:
        if userIsAdmin(db, user):
            foundRecords = list(
                dbRetrieveRecordsByKey(
                    db,
                    'box_role_permissions',
                    {
                        'box_id': thisBox.box_id,
                        'role_class': roleClass,
                        'role_id': roleId,
                    },
                    dbTablesDesc=dbSchema,
                )
            )
            if len(foundRecords) > 0:
                foundBRP = BoxRolePermission(**foundRecords[0])
                lBit = bit.lower()
                newBRPDict = recursivelyMergeDictionaries(
                    {lBit: 1 if not foundBRP.booleanBit(lBit) else 0},
                    defaultMap={
                        k: v
                        for k, v in foundBRP.asDict().items()
                        if k in {'box_id', 'role_class', 'role_id'}
                    },
                )
                try:
                    dbUpdateRecordOnTable(
                        db,
                        'box_role_permissions',
                        newBRPDict,
                        dbTablesDesc=dbSchema,
                        allowPartial=True,
                    )
                    if not skipCommit:
                        db.commit()
                except Exception as e:
                    db.rollback()
                    raise e
            else:
                raise OstracionError('Box role permission does not exist')
        else:
            raise OstracionError('Insufficient permissions')


def updateRolePermissionsDownPath(accumulated, newLayer):
    """ Update the (inherited + explicit) permission sets on a box.

        This is a single step of the progressive accumulation
        all the way from root down to the target box:
        * explicit have precedence over inherited,
        * both inputs, as well as output, are lists of box-role-permissions.
    """
    accumulatedMap = {
        acP.roleKey(): acP
        for acP in accumulated
    }
    newLayerMap = {
        acP.roleKey(): acP
        for acP in newLayer
    }
    finalPermissions = [
        [
            brP
            for brP in [
                newLayerMap.get(rKey),
                accumulatedMap.get(rKey),
            ]
            if brP is not None
        ][0]
        for rKey in accumulatedMap.keys() | newLayerMap.keys()
    ]
    #
    return finalPermissions


def userHasPermission(db, user, permissions, permissionBit):
    """ Check whether a user has a certain permission bit
        (essentially by exploiting a pre-done JOIN over the user roles).

        User:           is an object having .roles
        permissions:    is a list of permission objects
        permissionBit:  is in {'r','w','c'}
    """
    userRoles = generalisedGetUserRoles(db, user)
    roleKeySet = {r.roleKey() for r in userRoles}
    return any((
        p.booleanBit(permissionBit)
        for p in permissions
        if p.roleKey() in roleKeySet
    ))


def dbGetAllRoles(db, user):
    """ Get all available roles.
        Only users with the admin role can do this.
    """
    if userIsAdmin(db, user):
        return (
            Role(**r)
            for r in dbRetrieveAllRecords(
                db,
                'roles',
                dbTablesDesc=dbSchema,
            )
        )
    else:
        raise OstracionError('Insufficient permissions')


def _accumulateReadabilityLayers(roleKeySets, pathsToAccumulate):
    """ Accumulate the 'r' permission bit across roles:
        recursively handle the next item in the path,
        which is a set of "new roles at least one of which is required".
        The accumulation proceeds by calculating all set-of-roles S_i
        such that any user having at least one S_i, completely (all roles)
        has read access.
    """
    if len(pathsToAccumulate) == 0:
        return roleKeySets
    else:
        newRoleKeySets = orderPreservingUniquifyList(
            [
                rs | {brp.roleKey()}
                for rs in roleKeySets
                for brp in pathsToAccumulate[0]
                if brp.booleanBit('r')
            ],
            keyer=_roleSetSorter,
        )
        return _removeRedundantRoleSets(
            _removeObviousRoleSets(
                _accumulateReadabilityLayers(
                    newRoleKeySets,
                    pathsToAccumulate[1:],
                )
            )
        )


def _removeRedundantRoleSets(roleSetPool, chosenRoleSets=[]):
    """ For the sake of a compact presentation, once the full read-access
        algebra is computed for a box, remove the redundant information.

        Example: if the role sets giving R access to a box are
            {r1}
            {r2}
            {r1+r2}
            {r3}
            {r2+r3}
            {r4+r5}
        there is no need to give sets which are supersets of smaller ones,
        so this reduction gives
            {r1}
            {r2}
            {r3}
            {r4+r5}
    """
    if len(roleSetPool) == 0:
        return chosenRoleSets
    else:
        #
        sortedRoleSetPool = sorted(
            roleSetPool,
            key=_roleSetSorter,
        )
        shortestRoleSetInPool = sortedRoleSetPool[0]
        remainingRoleSets = [
            rs
            for rs in sortedRoleSetPool[1:]
            if len(shortestRoleSetInPool-rs) > 0
        ]
        return _removeRedundantRoleSets(
            remainingRoleSets,
            chosenRoleSets + [shortestRoleSetInPool],
        )


def _removeObviousRoleSets(roleSets):
    """ Take care of removing, for the sake of concise presentation,
        role sets which are not only, but contain, 'anonymous'.
    """
    okRoleSets = orderPreservingUniquifyList(
        sorted(
            [
                (rs
                 if len(rs) == 1
                 else {_r for _r in rs if _r != ('system', 'anonymous')})
                for rs in roleSets
            ],
            key=_roleSetSorter,
        ),
        keyer=_roleSetSorter,
    )
    return okRoleSets


def calculateBoxPermissionAlgebra(pHistory, boxPermissions):
    """ Calculate the complete permission algebra (of a box B)
        given the history of permission sets collected from root to B
        and the permissions (inherited + explicit) of B itself.

        The result is a map from each permission bit ('r','w','c')
        to a list of set of roles such that users who have
        all roles of at least one of these sets will be granted
        that permission.
    """
    initialRoleKeySets = [
        {brp.roleKey()}
        for brp in pHistory[0]
        if brp.booleanBit('r')
    ]
    readabilityPath = pHistory[1:]
    readAccessKeySets = _accumulateReadabilityLayers(
        initialRoleKeySets,
        readabilityPath,
    )
    finalReadAccessKeySets = _removeObviousRoleSets(readAccessKeySets)
    # armed with the read permissions we calculate the W and C permissions
    writeAccessKeySets = orderPreservingUniquifyList(
        [
            rs | {brp.roleKey()}
            for rs in readAccessKeySets
            for brp in boxPermissions
            if brp.booleanBit('w')
        ],
        keyer=_roleSetSorter,
    )
    finalWriteAccessKeySets = _removeRedundantRoleSets(
        _removeObviousRoleSets(
            writeAccessKeySets
        )
    )
    changeAccessKeySets = orderPreservingUniquifyList(
        [
            rs | {brp.roleKey()}
            for rs in readAccessKeySets
            for brp in boxPermissions
            if brp.booleanBit('c')
        ],
        keyer=_roleSetSorter,
    )
    finalChangeAccessKeySets = _removeRedundantRoleSets(
        _removeObviousRoleSets(
            changeAccessKeySets
        )
    )
    #
    return {
        'r': finalReadAccessKeySets,
        'w': finalWriteAccessKeySets,
        'c': finalChangeAccessKeySets,
    }
