""" accountingTools.py
    Accounting-related database operations.
"""

import datetime

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries
)
from ostracion_app.utilities.tools.extraction import safeNone

from ostracion_app.views.apps.accounting.models.Actor import Actor
from ostracion_app.views.apps.accounting.models.\
    LedgerMovementContribution import LedgerMovementContribution
from ostracion_app.views.apps.accounting.models.LedgerMovement import (
    LedgerMovement,
)
from ostracion_app.views.apps.accounting.models.Ledger import Ledger
from ostracion_app.views.apps.accounting.models.LedgerUser import LedgerUser
from ostracion_app.views.apps.accounting.models.MovementCategory import (
    MovementCategory,
)
from ostracion_app.views.apps.accounting.models.MovementSubcategory import (
    MovementSubcategory,
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.database.permissions import (
    userHasRole,
    userIsAdmin,
)

from ostracion_app.utilities.database.userTools import dbGetUser

from ostracion_app.utilities.database.sqliteEngine import (
    dbRetrieveAllRecords,
    dbAddRecordToTable,
    dbRetrieveRecordByKey,
    dbUpdateRecordOnTable,
    dbDeleteRecordsByKey,
    dbRetrieveRecordsByKey,
    dbCountRecordsByKey,
)
from ostracion_app.utilities.database.dbSchema import (
    dbSchema,
)


# helper functions
def ledgerQueryToWhereClauses(q):
    """Make a (dict) ledger-query into a whereClauses array."""
    _desc = safeNone(q.get('description'), '')
    return [
        # fieldvalue-based query parts
        qPair
        for qPair in (
            (qPhrase, q.get(qFName))
            for qPhrase, qFName in (
                ('date>=?', 'dateFrom'),
                ('date<=?', 'dateTo'),
                ('category_id=?', 'categoryId'),
                ('subcategory_id=?', 'subcategoryId'),
            )
        )
        if qPair[1] is not None
    ] + [
        # particular constructs
        qLitPair
        for qLitPair in (
            (
                'description LIKE ?',
                (
                    '%%%s%%' % _desc
                    if _desc != ''
                    else None
                ),
            ),
        )
        if qLitPair[1] is not None
    ]


def dbGetLedger(db, user, ledgerId):
    """Retrieve ledger given its id."""
    ledgerDict = dbRetrieveRecordByKey(
        db,
        'accounting_ledgers',
        {'ledger_id': ledgerId},
        dbTablesDesc=dbSchema,
    )
    if ledgerDict is None:
        return None
    else:
        # permission check
        ledger = Ledger(**ledgerDict)
        if userIsAdmin(db, user):
            return ledger
        else:
            # is the user allowed to see this ledger?
            ledgerUserDict = dbRetrieveRecordByKey(
                db,
                'accounting_ledgers_users',
                {'ledger_id': ledgerId, 'username': user.username},
                dbTablesDesc=dbSchema,
            )
            if ledgerUserDict is not None:
                return ledger
            else:
                raise OstracionError('Insufficient permissions')


def dbCreateLedger(db, user, newLedger):
    """Create a new ledger row."""
    if newLedger.creator_username == user.username and userIsAdmin(db, user):
        dbAddRecordToTable(
            db,
            'accounting_ledgers',
            newLedger.asDict(),
            dbTablesDesc=dbSchema,
        )
        #
        dbTouchLedger(db, user, newLedger, skipCommit=True)
        db.commit()
    else:
        raise OstracionError('Insufficient permissions')


def dbUpdateLedger(db, user, newLedger, skipCommit=False):
    """Update an existing ledger row."""
    if userIsAdmin(db, user):
        dbUpdateRecordOnTable(
            db,
            'accounting_ledgers',
            newLedger.asDict(),
            dbTablesDesc=dbSchema,
        )
        dbTouchLedger(db, user, newLedger, skipCommit=True)
        if not skipCommit:
            db.commit()
    else:
        raise OstracionError('Insufficient permissions')


def dbUserCanSeeLedger(db, user, ledgerId):
    return dbRetrieveRecordByKey(
        db,
        'accounting_ledgers_users',
        {
            'ledger_id': ledgerId,
            'username': user.username,
        },
        dbTablesDesc=dbSchema,
    ) is not None


def dbGetAllLedgers(db, user):
    """Get an iterable listing of all existing ledgers."""
    if userIsAdmin(db, user):
        return (
            Ledger(**l)
            for l in dbRetrieveAllRecords(
                db,
                'accounting_ledgers',
                dbTablesDesc=dbSchema,
            )
        )
    else:
        if userHasRole(db, user, 'app', 'accounting'):
            return (
                Ledger(**l)
                for l in dbRetrieveAllRecords(
                    db,
                    'accounting_ledgers',
                    dbTablesDesc=dbSchema,
                )
                if dbUserCanSeeLedger(db, user, l['ledger_id'])
            )
        else:
            raise OstracionError('Insufficient permissions')


def dbDeleteLedger(db, user, ledger):
    """
        Delete a ledger and all its sibling rows in
        foreign-key-related tables.
    """
    if userIsAdmin(db, user):
        # delete rows from all related tables
        for relatedTableName in [
            'accounting_movement_contributions',
            'accounting_ledger_movements',
            'accounting_movement_subcategories',
            'accounting_movement_categories',
            'accounting_actors',
            'accounting_ledgers_users',
        ]:
            dbDeleteRecordsByKey(
                db,
                relatedTableName,
                {'ledger_id': ledger.ledger_id},
                dbTablesDesc=dbSchema,
            )
        # delete the ledger itself
        dbDeleteRecordsByKey(
            db,
            'accounting_ledgers',
            {'ledger_id': ledger.ledger_id},
            dbTablesDesc=dbSchema,
        )
        db.commit()
    else:
        raise OstracionError('Insufficient permissions')


def dbGetUsersForLedger(db, user, ledger):
    """Return an iterable of the users subscribed to a ledger."""
    if userIsAdmin(db, user) or dbUserCanSeeLedger(db, user, ledger.ledger_id):
        return (
            dbGetUser(
                db,
                LedgerUser(**l).username,
            )
            for l in dbRetrieveRecordsByKey(
                db,
                'accounting_ledgers_users',
                {'ledger_id': ledger.ledger_id},
                dbTablesDesc=dbSchema,
            )
        )
    else:
        raise OstracionError('Insufficient permissions')


def dbGetLedgerUser(db, user, ledger, username):
    """Return a relation row user/ledger."""
    ledgerUserDict = dbRetrieveRecordByKey(
        db,
        'accounting_ledgers_users',
        {'ledger_id': ledger.ledger_id, 'username': username},
        dbTablesDesc=dbSchema,
    )
    return LedgerUser(**ledgerUserDict) if ledgerUserDict is not None else None


def dbAddUserToLedger(db, user, ledger, userToAdd):
    """Subscribe a user to a ledger. Raise error if already subscribed."""
    rel = dbGetLedgerUser(db, user, ledger, userToAdd.username)
    if rel is None:
        # adding the relation
        newLedgerUser = LedgerUser(
            ledger_id=ledger.ledger_id,
            username=userToAdd.username,
        )
        dbAddRecordToTable(
            db,
            'accounting_ledgers_users',
            newLedgerUser.asDict(),
            dbTablesDesc=dbSchema,
        )
        dbTouchLedger(db, user, ledger, skipCommit=True)
        #
        db.commit()
    else:
        raise OstracionError('User already subscribed to ledger')


def dbRemoveUserFromLedger(db, user, ledger, userToRemove):
    """Subscribe a user to a ledger. Raise error if already subscribed."""
    rel = dbGetLedgerUser(db, user, ledger, userToRemove.username)
    if rel is not None:
        # removing the relation
        dbDeleteRecordsByKey(
            db,
            'accounting_ledgers_users',
            {
                'ledger_id': rel.ledger_id,
                'username': rel.username,
            },
            dbTablesDesc=dbSchema,
        )
        dbTouchLedger(db, user, ledger, skipCommit=True)
        #
        db.commit()
    else:
        raise OstracionError('User already not subscribed to ledger')


def dbGetActorsForLedger(db, user, ledger):
    """Return an iterable of Actor objects for a ledger."""
    return (
        Actor(**l)
        for l in dbRetrieveRecordsByKey(
            db,
            'accounting_actors',
            {'ledger_id': ledger.ledger_id},
            dbTablesDesc=dbSchema,
        )
    )


def dbAddActorToLedger(db, user, ledger, newActor):
    """Add and actor to a ledger."""
    actor = dbGetActor(db, user, ledger.ledger_id, newActor.actor_id)
    if actor is None:
        dbAddRecordToTable(
            db,
            'accounting_actors',
            newActor.asDict(),
            dbTablesDesc=dbSchema,
        )
        dbTouchLedger(db, user, ledger, skipCommit=True)
        #
        db.commit()
    else:
        raise OstracionError('Actor exists already')


def dbGetActor(db, user, ledgerId, actorId):
    """Retrieve a single actor by its key."""
    actorDict = dbRetrieveRecordByKey(
        db,
        'accounting_actors',
        {'ledger_id': ledgerId, 'actor_id': actorId},
        dbTablesDesc=dbSchema,
    )
    if actorDict is None:
        return None
    else:
        return Actor(**actorDict)


def dbDeleteActor(db, user, ledger, actor):
    """Delete an actor from a ledger."""
    if userIsAdmin(db, user):
        # TODO delete rows from other related tables
        dbDeleteRecordsByKey(
            db,
            'accounting_actors',
            {'ledger_id': ledger.ledger_id, 'actor_id': actor.actor_id},
            dbTablesDesc=dbSchema,
        )
        dbTouchLedger(db, user, ledger, skipCommit=True)
        #
        db.commit()
    else:
        raise OstracionError('Insufficient permissions')


def dbGetCategoriesForLedger(db, user, ledger):
    """Return an iterable of MovementCategory objects for a ledger."""
    return (
        MovementCategory(**l)
        for l in dbRetrieveRecordsByKey(
            db,
            'accounting_movement_categories',
            {'ledger_id': ledger.ledger_id},
            dbTablesDesc=dbSchema,
        )
    )


def dbGetCategory(db, user, ledgerId, categoryId):
    """Retrieve a single movement category by its key."""
    categoryDict = dbRetrieveRecordByKey(
        db,
        'accounting_movement_categories',
        {'ledger_id': ledgerId, 'category_id': categoryId},
        dbTablesDesc=dbSchema,
    )
    if categoryDict is None:
        return None
    else:
        return MovementCategory(**categoryDict)


def dbGetSubcategory(db, user, ledgerId, categoryId, subcategoryId):
    """Retrieve a single movement subcategory by its key."""
    subcategoryDict = dbRetrieveRecordByKey(
        db,
        'accounting_movement_subcategories',
        {
            'ledger_id': ledgerId,
            'category_id': categoryId,
            'subcategory_id': subcategoryId,
        },
        dbTablesDesc=dbSchema,
    )
    if subcategoryDict is None:
        return None
    else:
        return MovementSubcategory(**subcategoryDict)


def dbAddCategoryToLedger(db, user, ledger, newCategory):
    """Add a MovementCategory under a given ledger."""
    if newCategory.ledger_id == ledger.ledger_id:
        category = dbGetCategory(db, user, ledger.ledger_id,
                                 newCategory.category_id)
        if category is None:
            dbAddRecordToTable(
                db,
                'accounting_movement_categories',
                newCategory.asDict(),
                dbTablesDesc=dbSchema,
            )
            dbTouchLedger(db, user, ledger, skipCommit=True)
            #
            db.commit()
        else:
            raise OstracionError('Category exists already')
    else:
        raise OstracionError('Illegitimate category')


def dbAddSubcategoryToLedger(db, user, ledger, newSubcategory):
    """
        Add a MovementSubcategory under a given ledger.
        The corresponding category must exist.
    """
    if ledger.ledger_id == newSubcategory.ledger_id:
        category = dbGetCategory(db, user, ledger.ledger_id,
                                 newSubcategory.category_id)
        if category is not None:
            dbAddRecordToTable(
                db,
                'accounting_movement_subcategories',
                newSubcategory.asDict(),
                dbTablesDesc=dbSchema,
            )
            dbTouchLedger(db, user, ledger, skipCommit=True)
            #
            db.commit()
        else:
            raise OstracionError('Unknown category')
    else:
        raise OstracionError('Illegitimate category')


def dbGetSubcategoriesForLedger(db, user, ledger, category):
    """
        Give an iterable of MovementSubcategory objects for a ledger/category.
    """
    return (
        MovementSubcategory(**l)
        for l in dbRetrieveRecordsByKey(
            db,
            'accounting_movement_subcategories',
            {
                'ledger_id': ledger.ledger_id,
                'category_id': category.category_id,
            },
            dbTablesDesc=dbSchema,
        )
    )


def dbUpdateCategoryInLedger(db, user, ledger, newCategory, skipCommit=False):
    """Update a ledger movement category."""
    if ledger.ledger_id != newCategory.ledger_id:
        raise OstracionError('Ledger mismatch')
    else:
        dbUpdateRecordOnTable(
            db,
            'accounting_movement_categories',
            newCategory.asDict(),
            dbTablesDesc=dbSchema,
        )
        dbTouchLedger(db, user, ledger, skipCommit=True)
        if not skipCommit:
            db.commit()


def dbUpdateSubcategoryInLedger(db, user, ledger, category, newSubcategory,
                                skipCommit=False):
    """Update a ledger movement subcategory."""
    if ledger.ledger_id != category.ledger_id:
        raise OstracionError('Ledger mismatch')
    elif ledger.ledger_id != newSubcategory.ledger_id:
        raise OstracionError('Ledger mismatch')
    elif category.category_id != newSubcategory.category_id:
        raise OstracionError('Category mismatch')
    else:
        dbUpdateRecordOnTable(
            db,
            'accounting_movement_subcategories',
            newSubcategory.asDict(),
            dbTablesDesc=dbSchema,
        )
        dbTouchLedger(db, user, ledger, skipCommit=True)
        if not skipCommit:
            db.commit()


def dbDeleteSubcategoryFromLedger(db, user, ledger, category, subcategory,
                                  skipCommit=False):
    dbDeleteRecordsByKey(
        db,
        'accounting_movement_subcategories',
        {
            'ledger_id': ledger.ledger_id,
            'category_id': category.category_id,
            'subcategory_id': subcategory.subcategory_id,
        },
        dbTablesDesc=dbSchema,
    )
    dbTouchLedger(db, user, ledger, skipCommit=True)
    if not skipCommit:
        db.commit()


def dbDeleteCategoryFromLedger(db, user, ledger, category,
                               skipCommit=False):
    dbDeleteRecordsByKey(
        db,
        'accounting_movement_categories',
        {
            'ledger_id': ledger.ledger_id,
            'category_id': category.category_id,
        },
        dbTablesDesc=dbSchema,
    )
    dbTouchLedger(db, user, ledger, skipCommit=True)
    if not skipCommit:
        db.commit()


def dbEraseCategoryFromLedger(db, user, ledger, category):
    """Clear a whole category from a ledger setup, incl. subcats."""
    subCats = dbGetSubcategoriesForLedger(db, user, ledger, category)
    for sCat in subCats:
        dbDeleteSubcategoryFromLedger(
            db,
            user,
            ledger,
            category,
            sCat,
            skipCommit=True,
        )
    dbDeleteCategoryFromLedger(
        db,
        user,
        ledger,
        category,
        skipCommit=True,
    )
    dbTouchLedger(db, user, ledger, skipCommit=True)
    db.commit()


def dbMoveCategoryInLedger(db, user, ledger, category, direction):
    """
        Move 'up'/'down' a category within a ledger by reshuffling the indices.
    """
    allCategories = sorted(
        dbGetCategoriesForLedger(db, user, ledger),
        key=lambda cat: cat.sort_index,
    )
    moveeIndices = [
        catI
        for catI, cat in enumerate(allCategories)
        if cat.category_id == category.category_id
    ]
    if len(moveeIndices) > 0:
        # the moving: reindexing map
        moveeIndex = moveeIndices[0]
        if direction == 'down':
            if moveeIndex + 1 >= len(allCategories):
                reMap = {}
            else:
                reMap = {
                    moveeIndex: moveeIndex + 1,
                    moveeIndex + 1: moveeIndex,
                }
        elif direction == 'up':
            if moveeIndex <= 0:
                reMap = {}
            else:
                reMap = {
                    moveeIndex: moveeIndex - 1,
                    moveeIndex - 1: moveeIndex,
                }
        else:
            raise OstracionError('Unknown direction')
        # the actual overwriting of sort_index
        for catIndex, cat in enumerate(allCategories):
            newIndex = reMap.get(catIndex, catIndex)
            newCat = MovementCategory(**recursivelyMergeDictionaries(
                {
                    'sort_index': newIndex,
                },
                defaultMap=cat.asDict(),
            ))
            dbUpdateCategoryInLedger(db, user, ledger, newCat, skipCommit=True)
        #
        dbTouchLedger(db, user, ledger, skipCommit=True)
        db.commit()
    else:
        raise OstracionError('Unknown category')


def dbMoveSubcategoryInLedger(db, user, ledger, category, subcategory,
                              direction):
    """
        Move 'up'/'down' a subcat. within a ledger by reshuffling the indices.
    """
    allSubcategories = sorted(
        dbGetSubcategoriesForLedger(db, user, ledger, category),
        key=lambda subcat: subcat.sort_index,
    )
    moveeIndices = [
        scatI
        for scatI, scat in enumerate(allSubcategories)
        if scat.subcategory_id == subcategory.subcategory_id
    ]
    if len(moveeIndices) > 0:
        # the moving: reindexing map
        moveeIndex = moveeIndices[0]
        if direction == 'down':
            if moveeIndex + 1 >= len(allSubcategories):
                reMap = {}
            else:
                reMap = {
                    moveeIndex: moveeIndex + 1,
                    moveeIndex + 1: moveeIndex,
                }
        elif direction == 'up':
            if moveeIndex <= 0:
                reMap = {}
            else:
                reMap = {
                    moveeIndex: moveeIndex - 1,
                    moveeIndex - 1: moveeIndex,
                }
        else:
            raise OstracionError('Unknown direction')
        # the actual overwriting of sort_index
        for scatIndex, scat in enumerate(allSubcategories):
            newIndex = reMap.get(scatIndex, scatIndex)
            newSubcat = MovementSubcategory(**recursivelyMergeDictionaries(
                {
                    'sort_index': newIndex,
                },
                defaultMap=scat.asDict(),
            ))
            dbUpdateSubcategoryInLedger(db, user, ledger, category, newSubcat,
                                        skipCommit=True)
        #
        dbTouchLedger(db, user, ledger, skipCommit=True)
        db.commit()
    else:
        raise OstracionError('Unknown subcategory')


def dbTouchLedger(db, user, ledger, skipCommit=False):
    """Update last_edit_date and last_edit_username of a ledger."""
    if userIsAdmin(db, user) or dbUserCanSeeLedger(db, user, ledger.ledger_id):
        dbUpdateRecordOnTable(
            db,
            'accounting_ledgers',
            {
                'ledger_id': ledger.ledger_id,
                'last_edit_date': datetime.datetime.now(),
                'last_edit_username': user.username,
            },
            dbTablesDesc=dbSchema,
            allowPartial=True,
        )
        if not skipCommit:
            db.commit()
    else:
        raise OstracionError('Insufficient permissions')


def dbAddFullMovementToLedger(db, user, ledger, newMovement, newContributions):
    """
        Add new movement+contributions to a ledger.
        newContributions is a map actor_id -> contribution object.
    """
    if userIsAdmin(db, user) or dbUserCanSeeLedger(db, user, ledger.ledger_id):
        if ledger.ledger_id == newMovement.ledger_id:
            # can insert, proceed
            if all(c.movement_id == newMovement.movement_id
                    for c in newContributions.values()):
                dbAddRecordToTable(
                    db,
                    'accounting_ledger_movements',
                    newMovement.asDict(),
                    dbTablesDesc=dbSchema,
                )
                for contrib in newContributions.values():
                    dbAddRecordToTable(
                        db,
                        'accounting_movement_contributions',
                        contrib.asDict(),
                        dbTablesDesc=dbSchema,
                    )
                dbTouchLedger(db, user, ledger, skipCommit=True)
                #
                db.commit()
            else:
                raise OstracionError('Malformed movement insertion')
        else:
            raise OstracionError('Malformed movement insertion')
    else:
        raise OstracionError('Insufficient permissions')


def dbUpdateFullMovementInLedger(db, user, ledger, newMovement,
                                 newContributions):
    """
        Update new movement+contributions of a ledger.
        Same as 'add' but assumes movement (and its contribs) exist(s) already.
    """
    if userIsAdmin(db, user) or dbUserCanSeeLedger(db, user, ledger.ledger_id):
        if ledger.ledger_id == newMovement.ledger_id:
            # are all actors on DB passed to this update?
            actorIdsOnDB = {
                contribDict['actor_id']
                for contribDict in dbRetrieveRecordsByKey(
                    db,
                    'accounting_movement_contributions',
                    {
                        'ledger_id': ledger.ledger_id,
                        'movement_id': newMovement.movement_id,
                    },
                    dbTablesDesc=dbSchema,
                )
            }
            actorsIdsInNewContrib = {
                nContrib.actor_id
                for nContrib in newContributions.values()
            }
            actorIdsLeftOut = actorIdsOnDB - actorsIdsInNewContrib
            if len(actorIdsLeftOut) == 0:
                # can insert, proceed
                if all(c.movement_id == newMovement.movement_id
                        for c in newContributions.values()):
                    dbUpdateRecordOnTable(
                        db,
                        'accounting_ledger_movements',
                        newMovement.asDict(),
                        dbTablesDesc=dbSchema,
                    )
                    for contrib in newContributions.values():
                        if contrib.actor_id in actorIdsOnDB:
                            dbUpdateRecordOnTable(
                                db,
                                'accounting_movement_contributions',
                                contrib.asDict(),
                                dbTablesDesc=dbSchema,
                            )
                        else:
                            dbAddRecordToTable(
                                db,
                                'accounting_movement_contributions',
                                contrib.asDict(),
                                dbTablesDesc=dbSchema,
                            )
                    dbTouchLedger(db, user, ledger, skipCommit=True)
                    #
                    db.commit()
            else:
                raise OstracionError('Actors mismatch in movement update')
        else:
            raise OstracionError('Malformed movement insertion')
    else:
        raise OstracionError('Insufficient permissions')


def _makeFullMovementStructure(_db, _ledger, _movdict):
    """wrap a ledger movement in a structure describing also its contribs."""
    movement = LedgerMovement(**_movdict)
    contribQuery = dbRetrieveRecordsByKey(
        _db,
        'accounting_movement_contributions',
        {
            'ledger_id': _ledger.ledger_id,
            'movement_id': movement.movement_id,
        },
        dbTablesDesc=dbSchema,
    )
    contributions = {
        contrib.actor_id: contrib
        for contrib in (
            LedgerMovementContribution(**_condict)
            for _condict in contribQuery
        )
    }
    contribPropSum = sum(con.proportion for con in contributions.values())
    return {
        'movement': movement,
        'contributions': contributions,
        'contribution_prop_total': contribPropSum,
    }


def dbGetLedgerFullMovements(db, user, ledger, query={}, pageSize=None,
                             pageStart=None):
    """
        *TEMPORARY*, will have query driver, pagination, joins.
        Retrieve movements pertaining to a given ledger.

        pageSize = None if infinite
    """
    if userIsAdmin(db, user) or dbUserCanSeeLedger(db, user, ledger.ledger_id):
        queryWhereClauses = ledgerQueryToWhereClauses(query)
        bareMovQuery = dbRetrieveRecordsByKey(
            db,
            'accounting_ledger_movements',
            {
                'ledger_id': ledger.ledger_id,
            },
            dbTablesDesc=dbSchema,
            order=[
                ('date', 'DESC'),
                ('last_edit_date', 'DESC'),
            ],
            whereClauses=queryWhereClauses,
            limit=pageSize,
            offset=pageStart,
        )
        return [
            _makeFullMovementStructure(db, ledger, bareMovDict)
            for bareMovDict in bareMovQuery
        ]
    else:
        raise OstracionError('Insufficient permissions')


def dbCountLedgerFullMovements(db, user, ledger, query={}):
    """
        *TEMPORARY* will have querying
        Count total number of movements [on a query] in a ledger
    """
    queryWhereClauses = ledgerQueryToWhereClauses(query)
    return dbCountRecordsByKey(
        db,
        'accounting_ledger_movements',
        {
            'ledger_id': ledger.ledger_id,
        },
        whereClauses=queryWhereClauses,
        dbTablesDesc=dbSchema,
    )


def dbGetLedgerFullMovement(db, user, ledger, movementId):
    """
        *TEMPORARY*, will have query driver, pagination, joins.
        Retrieve a single movement pertaining to a given ledger.
    """
    if userIsAdmin(db, user) or dbUserCanSeeLedger(db, user, ledger.ledger_id):
        bareMovDict = dbRetrieveRecordByKey(
            db,
            'accounting_ledger_movements',
            {
                'ledger_id': ledger.ledger_id,
                'movement_id': movementId,
            },
            dbTablesDesc=dbSchema,
        )
        if bareMovDict is None:
            return None
        else:
            return _makeFullMovementStructure(db, ledger, bareMovDict)
    else:
        raise OstracionError('Insufficient permissions')


def dbDeleteLedgerFullMovement(db, user, ledger, movement, skipCommit=False):
    """Delete a ledger movement and all its contributions."""
    dbDeleteRecordsByKey(
        db,
        'accounting_movement_contributions',
        {
            'ledger_id': ledger.ledger_id,
            'movement_id': movement.movement_id,
        },
        dbTablesDesc=dbSchema,
    )
    dbDeleteRecordsByKey(
        db,
        'accounting_ledger_movements',
        {
            'ledger_id': ledger.ledger_id,
            'movement_id': movement.movement_id,
        },
        dbTablesDesc=dbSchema,
    )
    dbTouchLedger(db, user, ledger, skipCommit=True)
    if not skipCommit:
        db.commit()
