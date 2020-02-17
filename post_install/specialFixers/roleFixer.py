""" roleFixer.py
    Special handling of the change in role-related
    tables, for a one-time postInstall alignment
"""


from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries,
)

from ostracion_app.utilities.database.sqliteEngine import (
    # dbOpenDatabase,
    dbCreateTable,
    dbAddRecordToTable,
    # dbUpdateRecordOnTable,
    # dbTableExists,
    dbQueryColumns,
    dbRetrieveAllRecords,
    dbRetrieveRecordByKey,
    dbDeleteTable,
)

from ostracion_app.utilities.database.dbSchema import (
    dbSchema,
    tableCreationOrder,
)


legacySchema = {
    'roles': {
        'primary_key': [
            ('role_id', 'TEXT'),
        ],
        'columns': [
            ('description', 'TEXT'),
            ('system', 'INTEGER'),
        ],
    },
    'box_role_permissions': {
        'primary_key': [
            ('box_id', 'TEXT'),
            ('role_id', 'TEXT'),
        ],
        'columns': [
            ('r', 'INTEGER'),
            ('w', 'INTEGER'),
            ('c', 'INTEGER'),
        ],
        'foreign_keys': {
            'boxes': [
                [['box_id'], ['box_id']],
            ],
            'roles': [
                [['role_id'], ['role_id']],
            ],
        },
    },
    'user_roles': {
        'primary_key': [
            ('username', 'TEXT'),
            ('role_id', 'TEXT'),
        ],
        'columns': [],
        'foreign_keys': {
            'users': [
                [['username'], ['username']],
            ],
            'roles': [
                [['role_id'], ['role_id']],
            ],
        },
    },
}


def tempTableName(tName):
    return '%s_transitional' % tName


def determineRoleClass(legacyRoleRecord):
    isSystem = legacyRoleRecord['system'] != 0
    return 'system' if isSystem else 'manual'

def convertRoleRelatedRecord(db, legacySchema,
                             srcTableName, inRecord):
    if srcTableName == 'roles':
        isSystem = inRecord['system'] != 0
        outRecord = {
            'role_id': inRecord['role_id'],
            'role_class': determineRoleClass(inRecord),
            # 'system' DISAPPEARS
            'description': inRecord['description'],
            'can_box': (
                0
                if isSystem and inRecord['role_id'] == 'ticketer'
                else 1
            ),
            'can_user': (
                0
                if isSystem and inRecord['role_id'] == 'anonymous'
                else 1
            ),
            'can_delete': 0 if isSystem else 1,
        }
        return outRecord
    elif srcTableName in {'box_role_permissions', 'user_roles'}:
        referenceRole = dbRetrieveRecordByKey(
            db,
            'roles',
            {'role_id': inRecord['role_id']},
            dbTablesDesc=legacySchema,
        )
        outRecord = recursivelyMergeDictionaries(
            {'role_class': determineRoleClass(referenceRole)},
            defaultMap=inRecord,
        )
        return outRecord
    else:
        raise NotImplementedError('Cannot translate records for table "%s"' % (
            srcTableName,
        ))


def fixRoleTablesAddingRoleClass(db):
    """ Deal with the schema changes
        to bring 'roles' from
            primary key = role_id
        to
            primary_key = (role_class, role_id)
        by acting on all involved tables
        while preserving the contents thereof.

        Returns whether it did something or not as a bool
    """
    roleColumns = dbQueryColumns(db, 'roles')
    mustAct = 'role_class' not in roleColumns and 'system' in roleColumns
    if not mustAct:
        return False
    else:
        print(' * Applying patch to roles')
        # get ready to dance
        targetSchema = {
            tempTableName(tName): tDesc
            for tName, tDesc in dbSchema.items()
            if tName in legacySchema
        }
        targetTableCreationOrder = {
            tempTableName(k): v
            for k, v in tableCreationOrder.items()
        }
        # create the transitional tables (new schema)
        for ntName, ntContents in sorted(
                targetSchema.items(),
                key=lambda tnc: targetTableCreationOrder[tnc[0]]):
            print('     * creating "%s" ' % ntName, end='')
            dbCreateTable(
                db,
                ntName,
                {k: v for k, v in ntContents.items() if k != 'foreign_keys'},
            )
            print('done.')
        # copy items table by table
        print('     * populating ...')
        for srcTName, srcSchema in sorted(
                legacySchema.items(),
                key=lambda tnc: tableCreationOrder[tnc[0]]):
            print('         - "%s" ...' % srcTName)
            # read all items from this srcTName and
            # copy it - with changes - onto tempTableName(srcTName)
            dstTName = tempTableName(srcTName)
            dstSchema = targetSchema[dstTName]
            for inRecordIndex, inRecord in enumerate(dbRetrieveAllRecords(
                db,
                srcTName,
                dbTablesDesc=legacySchema,
            )):
                print('             record[%i] ... ' % inRecordIndex, end='')
                outRecord = convertRoleRelatedRecord(db, legacySchema,
                                                     srcTName, inRecord)
                dbAddRecordToTable(
                    db,
                    dstTName,
                    outRecord,
                    dbTablesDesc=targetSchema,
                )
                print('inserted.')
            print('         - done "%s"' % srcTName)
        print('     * done populating.')
        # we drop the original tables and recreate them with the new schema
        print('     * dropping legacy tables ...')
        for srcTName, srcSchema in sorted(
                legacySchema.items(),
                key=lambda tnc: tableCreationOrder[tnc[0]],
                reverse=True):
            print('         - "%s" ... ' % srcTName, end='')
            dbDeleteTable(db, srcTName)
            print('dropped.')
        print('     * done dropping legacy tables.')
        # we recreate the tables with the new schema
        print('     * re-creating tables ...')
        for srcTName, _ in sorted(
                legacySchema.items(),
                key=lambda tnc: tableCreationOrder[tnc[0]]):
            print('         - "%s" ... ' % srcTName, end='')
            dbCreateTable(
                db,
                srcTName,
                dbSchema[srcTName],
            )
            print('re-created.')
        print('     * done re-creating tables.')
        # we populate the recreated tables with the temporary tables' contents
        print('     * repopulating tables ...')
        for srcTName, srcSchema in sorted(
                legacySchema.items(),
                key=lambda tnc: tableCreationOrder[tnc[0]]):
            print('         - "%s" ... ' % srcTName)
            for recordIndex, record in enumerate(dbRetrieveAllRecords(
                db,
                tempTableName(srcTName),
                dbTablesDesc=targetSchema,
            )):
                print('             record [%i] ... ' % recordIndex, end='')
                dbAddRecordToTable(
                    db,
                    srcTName,
                    record,
                    dbTablesDesc=dbSchema,
                )
                print('inserted.')
            print('         - done "%s"' % srcTName)
        print('     * done repopulating tables.')
        # we drop the temporary tables
        print('     * dropping temporary tables ...')
        for srcTName, srcSchema in sorted(
                legacySchema.items(),
                key=lambda tnc: tableCreationOrder[tnc[0]],
                reverse=True):
            print('         - "%s" ... ' % srcTName, end='')
            deleteeTName = tempTableName(srcTName)
            dbDeleteTable(db, deleteeTName)
            print('dropped.')
        print('     * done dropping temporary tables.')
        #
        return True
