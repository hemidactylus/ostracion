"""
    userDeletion.py
        TO DOC
"""

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries
)

from ostracion_app.utilities.database.sqliteEngine import (
    dbDeleteRecordsByKey,
    dbRetrieveRecordByKey,
    dbRetrieveAllRecords,
    dbUpdateRecordOnTable,
)
from ostracion_app.utilities.database.dbSchema import (
    dbSchema,
)

from ostracion_app.views.apps.accounting.accountingThumbnails import (
    updateLedgerThumbnail,
)

from ostracion_app.views.apps.accounting.models.Ledger import Ledger
from ostracion_app.views.apps.accounting.db.accountingTools import (
    dbGetLedger,
    dbUpdateLedger,
    dbGetAllLedgers,
    dbFindFirstAvailableLedgerName,
)


def accountingUserDeletion(db, username, user, fileStorageDirectory):
    """
        Handle deletion of a user throughout the accounting tables.
        This means that
          - the table with user grants to ledger loses records
          - all usernames contained in other tables (last edit, etc)
            are converted to the special '' username.
        No commit required at the end (it is taken care of by the caller).
    """
    fsDeleteQueue = []
    # delete rows relating users and ledgers
    dbDeleteRecordsByKey(
        db,
        'accounting_ledgers_users',
        {'username': username},
        dbTablesDesc=dbSchema,
    )
    # set referenced usernames to '' - I. ledgers
    ledgerFields = [
        'creator_username',
        'last_edit_username',
        'icon_file_id_username',
    ]
    allLedgerDicts = (
        l
        for l in dbRetrieveAllRecords(
            db,
            'accounting_ledgers',
            dbTablesDesc=dbSchema,
        )
    )
    for ledgerDict in allLedgerDicts:
        if any([ledgerDict[f] == username
                for f in ledgerFields]):
            #
            if ledgerDict['creator_username'] == username:
                ld1 = recursivelyMergeDictionaries(
                    {'creator_username': ''},
                    defaultMap=ledgerDict,
                )
            else:
                ld1 = ledgerDict
            #
            if ledgerDict['last_edit_username'] == username:
                # empty metadata as well
                newLedgerName = dbFindFirstAvailableLedgerName(
                    db,
                    prefix='REDACTED_LEDGER_',
                    suffix='',
                )
                ld2 = recursivelyMergeDictionaries(
                    {
                        'last_edit_username': '',
                        'name': newLedgerName,
                        'description': ('Ledger name redacted upon '
                                        'account deletion'),
                    },
                    defaultMap=ld1,
                )
            else:
                ld2 = ld1
            #
            if ledgerDict['icon_file_id_username'] == username:
                iconedLedger = Ledger(**ld2)
                fsDeleteQueue += updateLedgerThumbnail(
                    db,
                    iconedLedger,
                    None,
                    None,
                    user,
                    fileStorageDirectory=fileStorageDirectory,
                    accountDeletionInProgress=True,
                    skipCommit=True,
                )
                #
                newLedgerDict = recursivelyMergeDictionaries(
                    {
                        'icon_file_id': '',
                        'icon_mime_type': '',
                        'icon_file_id_username': '',
                    },
                    defaultMap=ld2,
                )
            else:
                newLedgerDict = ld2
            # finally save the new ledger
            dbUpdateRecordOnTable(
                db,
                'accounting_ledgers',
                newLedgerDict,
                dbTablesDesc=dbSchema,
            )
    # set referenced usernames to '' - II. ledger movements
    allLedgerMovementDicts = (
        l
        for l in dbRetrieveAllRecords(
            db,
            'accounting_ledger_movements',
            dbTablesDesc=dbSchema,
        )
    )
    for ledgerMovementDict in allLedgerMovementDicts:
        if ledgerMovementDict['last_edit_username'] == username:
            newLedgerMovementDict = recursivelyMergeDictionaries(
                {
                    'last_edit_username': '',
                    'description': (
                        'Redacted upon user deletion'
                        if ledgerMovementDict['description'] != ''
                        else ''
                    ),
                },
                defaultMap=ledgerMovementDict,
            )
            # and saved
            dbUpdateRecordOnTable(
                db,
                'accounting_ledger_movements',
                newLedgerMovementDict,
                dbTablesDesc=dbSchema,
            )
    # all done.
    return fsDeleteQueue
