#!/usr/bin/env python

""" postInstall.py
    Idempotent regeneration of the DB and the secret key.
    To be used:
        -   as a triggered post-install finalisation
        -   as an update upon an existing DB
                (e.g. a new release has more settings)
        -   (with the nuclear "-f" option) to ERASE and
            regenerate the whole DB and the secret key.
                (the latter to be used with extreme care)
"""

import sys
import os

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries,
)

from ostracion_app.utilities.database.sqliteEngine import (
    dbOpenDatabase,
    dbCreateTable,
    dbAddRecordToTable,
    dbUpdateRecordOnTable,
    dbTableExists,
    dbQueryColumns,
    dbRetrieveAllRecords,
    dbRetrieveRecordByKey,
)
from ostracion_app.utilities.database.dbSchema import (
    dbSchema,
    tableCreationOrder,
)

from ostracion_app.utilities.tools.securityCodes import makeSecretKey

from ostracion_app.utilities.models.Link import Link

from config import (
    dbFullName,
    basedir,
)

from ostracion_app.utilities.tools.formatting import (
    applyReplacementPairs,
)

from post_install.initialValues.defaultDb import initialDbValues
from post_install.specialFixers.roleFixer import fixRoleTablesAddingRoleClass

sensitiveConfigFileTemplate = applyReplacementPairs(
    open(
        os.path.join(basedir, 'sensitive_config_TEMPLATE.py')
    ).read(),
    [
        ('sensitive_config_TEMPLATE.py', 'sensitive_config.py'),
        (
            ('# SECRET_KEY = \'insert_a_very_unguessable_48char_'
             'secret_key_here\''),
            'SECRET_KEY = \'{skKey}\'',
        )
    ],
)


if __name__ == '__main__':
    sensitiveConfigFilename = os.path.join(basedir, 'sensitive_config.py')
    if '-f' in sys.argv[1:] or not os.path.isfile(dbFullName):
        if os.path.isfile(dbFullName):
            print(' * Deleting previous DB file... ', end='')
            os.remove(dbFullName)
            print('done.')
        if os.path.isfile(sensitiveConfigFilename):
            print(' * Deleting previous sensitive configuration... ', end='')
            os.remove(sensitiveConfigFilename)
            print('done.')
    #
    if not os.path.isfile(sensitiveConfigFilename):
        print(' * Creating sensitive configuration ... ', end='')
        newSkKey = makeSecretKey(nChars=48)
        with open(sensitiveConfigFilename, 'w') as scFile:
            scFile.write(sensitiveConfigFileTemplate.format(skKey=newSkKey))
        print('done.')

    print(
        ' * %s DB... ' % (
            'Opening' if os.path.isfile(dbFullName) else 'Creating'
        ),
        end='',
    )
    db = dbOpenDatabase(dbFullName)
    print('done.')
    # special pre-everything fixes if patches are needed
    fixRoleTablesAddingRoleClass(db)
    #
    print(' * Creating tables')
    for tName, tContents in sorted(
            dbSchema.items(),
            key=lambda tnc: tableCreationOrder[tnc[0]]):
        print('     * %-60s' % ('"%s" ' % tName), end='')
        tableFound = dbTableExists(db, tName)
        if not tableFound:
            print('creating...', end='')
            dbCreateTable(db, tName, tContents)
            print(' done', end='')
        else:
            print('already_there', end='')
        print('.')
        # record insertion
        if not tableFound:
            tcontents = initialDbValues.get(tName)
            if tcontents is not None:
                # ordinary new-table filling
                print('        * Populating')
                for item in tcontents['values']:
                    model = tcontents['model'](**item)
                    dbAddRecordToTable(
                        db,
                        tName,
                        model.asDict(),
                        dbTablesDesc=dbSchema,
                    )
                    print('            - %s' % model)
                print('        * done.')
        else:
            # special handling of some tables
            if tName == 'settings':
                # here we add new settings and refresh some fields of the
                # existing ones (namely all but 'value')
                tcontents = initialDbValues.get(tName)
                print('        * Refreshing')
                for item in tcontents['values']:
                    model = tcontents['model'](**item)
                    print('            - %s : ' % model, end='')
                    itemDictFound = dbRetrieveRecordByKey(
                        db,
                        tName,
                        {'group_id': item['group_id'], 'id': item['id']},
                        dbTablesDesc=dbSchema,
                    )
                    if itemDictFound is None:
                        # new: insert
                        print('inserting... ', end='')
                        dbAddRecordToTable(
                            db,
                            tName,
                            model.asDict(),
                            dbTablesDesc=dbSchema,
                        )
                        print('done ', end='')
                    else:
                        # careful override and update back
                        mergedDict = recursivelyMergeDictionaries(
                            {'value': itemDictFound['value']},
                            defaultMap=model.asDict(),
                        )
                        print('updating... ', end='')
                        dbUpdateRecordOnTable(
                            db,
                            tName,
                            mergedDict,
                            dbTablesDesc=dbSchema,
                        )
                        print('done ', end='')
                    print('#')
                print('        * done.')
            elif tName == 'links':
                # we may have to add a field
                columns = dbQueryColumns(db, tName)
                if 'title' not in columns:
                    # must add 'title' and upgrade existing records
                    print('        * Adding "title" column')
                    db.execute(
                        'ALTER TABLE links ADD COLUMN title TEXT;'
                    )
                    db.execute(
                        'ALTER TABLE links ADD COLUMN dvector_title TEXT;'
                    )
                    print('        * Upgrading entries ... ', end='')
                    #
                    tempSchema = recursivelyMergeDictionaries(
                        {
                            tName: {
                                'columns': [
                                    col
                                    for col in dbSchema[tName]['columns']
                                    if col[0] not in {'title', 'dvector_title'}
                                ]
                            }
                        },
                        defaultMap={tName: dbSchema[tName]},
                    )
                    for prevLinkEntryDict in dbRetrieveAllRecords(
                        db,
                        tName,
                        tempSchema,
                    ):
                        print('<', end='')
                        newLink = Link(**(
                            recursivelyMergeDictionaries(
                                {'title': prevLinkEntryDict['name']},
                                prevLinkEntryDict,
                            )
                        )).asDict()
                        print(newLink)
                        dbUpdateRecordOnTable(
                            db,
                            tName,
                            newLink,
                            dbTablesDesc=dbSchema,
                        )
                        print('*> ', end='')
                    #
                    print('\n          done.')
            elif tName == 'roles':
                # we add new roles, only if they do not exist at all
                tcontents = initialDbValues.get(tName)
                print('        * Refreshing')
                for item in tcontents['values']:
                    model = tcontents['model'](**item)
                    print('            - %s : ' % model, end='')
                    itemDictFound = dbRetrieveRecordByKey(
                        db,
                        tName,
                        {
                            'role_class': item['role_class'],
                            'role_id': item['role_id'],
                        },
                        dbTablesDesc=dbSchema,
                    )
                    if itemDictFound is None:
                        # new: insert
                        print('inserting... ', end='')
                        dbAddRecordToTable(
                            db,
                            tName,
                            model.asDict(),
                            dbTablesDesc=dbSchema,
                        )
                        print('done ', end='')
                    else:
                        print('already present ', end='')
                    print('#')
                print('        * done.')
            elif tName == 'users':
                # we may have to add a field
                columns = dbQueryColumns(db, tName)
                for colName in ['terms_accepted', 'terms_accepted_version']:
                    if colName not in columns:
                        # must add colName
                        print('        * Adding "%s" column' % colName)
                        db.execute(
                            'ALTER TABLE users ADD COLUMN %s TEXT;' % colName
                        )
                        print('          done.')
        # regardless of whether the table was new or not,
        # some on-table checks and finalisations
        if tName == 'user_roles':
            print('        * Checking user-roles')
            # for each existing user, make sure the user/role exists
            for userDict in dbRetrieveAllRecords(
                db,
                'users',
                dbTablesDesc=dbSchema,
            ):
                if userDict['username'] != '':
                    print(
                        '            - "%s" : ' % userDict['username'],
                        end='',
                    )
                    # existence of the role
                    itemDictFound = dbRetrieveRecordByKey(
                        db,
                        'roles',
                        {
                            'role_class': 'user',
                            'role_id': userDict['username'],
                        },
                        dbTablesDesc=dbSchema,
                    )
                    if itemDictFound is None:
                        print('adding role ... ', end='')
                        userRole = initialDbValues['roles']['model'](**{
                            'role_class': 'user',
                            'role_id': userDict['username'],
                            'description': '%s user-role' % (
                                userDict['username']
                            ),
                            'can_box': 1,
                            'can_user': 0,
                            'can_delete': 0,
                        })
                        dbAddRecordToTable(
                            db,
                            'roles',
                            userRole.asDict(),
                            dbTablesDesc=dbSchema,
                        )
                        print('done ', end='')
                    else:
                        print('already present ', end='')
                    # existence of the user-role entry
                    relItemDictFound = dbRetrieveRecordByKey(
                        db,
                        'user_roles',
                        {
                            'role_class': 'user',
                            'role_id': userDict['username'],
                            'username': userDict['username'],
                        },
                        dbTablesDesc=dbSchema,
                    )
                    if relItemDictFound is None:
                        print('adding user_role ... ', end='')
                        relModel = initialDbValues['user_roles']['model']
                        relUserRole = relModel(**{
                            'role_class': 'user',
                            'role_id': userDict['username'],
                            'username': userDict['username'],
                        })
                        dbAddRecordToTable(
                            db,
                            'user_roles',
                            relUserRole.asDict(),
                            dbTablesDesc=dbSchema,
                        )
                        print('done ', end='')
                    else:
                        print('already present ', end='')
                    print('#')
            #
            print('        * done.')
    # all done.
    db.commit()
