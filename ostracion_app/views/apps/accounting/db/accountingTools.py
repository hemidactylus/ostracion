""" accountingTools.py
    Accounting-related database operations.
"""

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

from ostracion_app.utilities.database.permissions import userIsAdmin

from ostracion_app.utilities.database.userTools import dbGetUser

from ostracion_app.utilities.database.sqliteEngine import (
    dbRetrieveAllRecords,
    dbAddRecordToTable,
    dbRetrieveRecordByKey,
    dbUpdateRecordOnTable,
    dbDeleteRecordsByKey,
    dbRetrieveRecordsByKey,
)
from ostracion_app.utilities.database.dbSchema import (
    dbSchema,
)


def dbGetLedger(db, ledgerId):
    """Retrieve ledger given its id."""
    ledgerDict = dbRetrieveRecordByKey(
        db,
        'accounting_ledgers',
        {'ledger_id': ledgerId},
        dbTablesDesc=dbSchema,
    )
    return Ledger(**ledgerDict) if ledgerDict is not None else None


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
        db.commit()
    else:
        raise OstracionError('Insufficient permissions')


def dbUpdateLedger(db, user, newLedger):
    """Update an existing ledger row."""
    if userIsAdmin(db, user):
        dbUpdateRecordOnTable(
            db,
            'accounting_ledgers',
            newLedger.asDict(),
            dbTablesDesc=dbSchema,
        )
        db.commit()
    else:
        raise OstracionError('Insufficient permissions')


def dbGetAllLedgers(db, user):
    """Get a listing of all existing ledgers."""
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
        raise OstracionError('Insufficient permissions')


def dbDeleteLedger(db, user, ledgerId):
    """
        Delete a ledger and all its sibling rows in
        foreign-key-related tables.
    """
    if userIsAdmin(db, user):
        # TODO delete rows from other related tables
        dbDeleteRecordsByKey(
            db,
            'accounting_ledgers',
            {'ledger_id': ledgerId},
            dbTablesDesc=dbSchema,
        )
        db.commit()
    else:
        raise OstracionError('Insufficient permissions')


def dbGetUsersForLedger(db, user, ledgerId):
    """Return a list of the users subscribed to a ledger."""
    if userIsAdmin(db, user):
        return (
            dbGetUser(
                db,
                LedgerUser(**l).username,
            )
            for l in dbRetrieveRecordsByKey(
                db,
                'accounting_ledgers_users',
                {'ledger_id': ledgerId},
                dbTablesDesc=dbSchema,
            )
        )
    else:
        raise OstracionError('Insufficient permissions')


def dbGetLedgerUser(db, user, ledgerId, username):
    """Return a relation row user/ledger."""
    ledgerUserDict = dbRetrieveRecordByKey(
        db,
        'accounting_ledgers_users',
        {'ledger_id': ledgerId, 'username': username},
        dbTablesDesc=dbSchema,
    )
    return LedgerUser(**ledgerUserDict) if ledgerUserDict is not None else None


def dbAddUserToLedger(db, user, ledger, userToAdd):
    """Subscribe a user to a ledger. Raise error if already subscribed."""
    rel = dbGetLedgerUser(db, user, ledger.ledger_id, userToAdd.username)
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
        #
        db.commit()
    else:
        raise OstracionError('User already subscribed to ledger')


def dbRemoveUserFromLedger(db, user, ledger, userToRemove):
    """Subscribe a user to a ledger. Raise error if already subscribed."""
    rel = dbGetLedgerUser(db, user, ledger.ledger_id, userToRemove.username)
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
        #
        db.commit()
    else:
        raise OstracionError('User already not subscribed to ledger')
