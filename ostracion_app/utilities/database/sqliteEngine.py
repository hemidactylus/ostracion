""" sqliteEngine.py
    Library to handle a sqlite database.

    Almost all functions require an argument "dbTablesDesc" describing the
    database schema. This is in the form (indices, foreign_keys optional):

        dbTablesDesc={
            'TABLENAME': {
                'primary_key': [
                    ('COLUMN', 'TYPE'),
                    ...
                ],
                'columns': [
                    ('COLUMN', 'TYPE'),
                    ...
                ],
                'indices': {
                    'INDEX_NAME': [
                        ('COLUMN', 'ASC/DESC'),
                        ...
                    ],
                    ...
                },
                'foreign_keys': {
                    'OTHER_TABLENAME': [
                        [['COLUMN_HERE',...],['COLUMN_THERE',...]],
                        ...
                    ],
                },
            },
        }

"""

import sqlite3 as lite
from operator import itemgetter

DB_DEBUG = False

# for moot 'limit' clause in selects (this is 2^63-1, i.e. a signed long max)
veryLargeIntegerName = '9223372036854775807'


def listColumns(tableName, dbTablesDesc=None):
    """ Read the table structure and return an *ordered*
        list of its fields.
    """
    colList = []
    if 'primary_key' in dbTablesDesc[tableName]:
        colList += map(itemgetter(0), dbTablesDesc[tableName]['primary_key'])
    colList += map(itemgetter(0), dbTablesDesc[tableName]['columns'])
    return colList


def dbQueryColumns(db, tableName):
    """ Perform an actual SQL query to obtain the
        names of the existing columns in the table.
    """
    tableQuery = db.execute(
        'SELECT sql FROM sqlite_master WHERE name=?;',
        (tableName,),
    )
    rawResult = list(tableQuery)[0][0]
    fParen = rawResult.find('(')
    lParen = rawResult[::-1].find('(')
    inDef = rawResult[fParen + 1:(-(lParen + 1))]
    parts = [
        pt
        for pt in (
            _pt.strip()
            for _pt in inDef.replace('\n', ', ').replace('\t', ', ').split(',')
        )
        if pt != ''
        if 'CREATE TABLE' not in pt.upper()
        if 'FOREIGN KEY' not in pt.upper()
        if 'PRIMARY KEY' not in pt.upper()
    ]
    splitParts = [
        tuple(p for p in pt.split(' ') if p != '')
        for pt in parts
    ]
    if any(len(sp) != 2 for sp in splitParts):
        raise RuntimeError('Describe table parsed def pair split mismatch')
    return dict(splitParts)


def dbCountRecords(db, tableName):
    """ Count the rows in a table.
        Not particularly fast: uses a SELECT COUNT(*) internally
    """
    cur = db.cursor()
    retVal = list(db.execute("SELECT COUNT (*) FROM %s" % tableName))
    if len(retVal) > 0:
        return retVal[0][0]
    else:
        return None


def dbAddRecordToTable(db, tableName, recordDict, dbTablesDesc=None):
    """INSERT a row to a table."""
    colList = listColumns(tableName, dbTablesDesc=dbTablesDesc)
    columnNames = ', '.join(listColumns(tableName, dbTablesDesc))
    #
    insertStatement = 'INSERT INTO %s (%s) VALUES (%s)' % (
        tableName,
        columnNames,
        ', '.join(['?']*len(colList))
    )
    insertValues = tuple(recordDict[k] for k in colList)
    #
    if DB_DEBUG:
        print('[dbAddRecordToTable] %s' % insertStatement)
        print('[dbAddRecordToTable] %s' % ','.join(
            '%s' % iv
            for iv in insertValues
        ))
    db.execute(insertStatement, insertValues)
    #
    return


def dbUpdateRecordOnTable(db, tableName, newDict,
                          dbTablesDesc=None, allowPartial=False):
    """UPDATE a row on a table. Can perform a partial update if required."""
    dbKeys = list(map(itemgetter(0), dbTablesDesc[tableName]['primary_key']))
    otherFields = list(map(itemgetter(0), dbTablesDesc[tableName]['columns']))
    updatePart = ', '.join(
        '%s=?' % of
        for of in otherFields
        if not allowPartial or of in newDict
    )
    updatePartValues = [
        newDict[of]
        for of in otherFields
        if not allowPartial or of in newDict
    ]
    whereClause = ' AND '.join('%s=?' % dbk for dbk in dbKeys)
    whereValues = [newDict[dbk] for dbk in dbKeys]
    updateStatement = 'UPDATE %s SET %s WHERE %s' % (
        tableName,
        updatePart,
        whereClause
    )
    updateValues = updatePartValues + whereValues
    if DB_DEBUG:
        print('[dbUpdateRecordOnTable] %s' % updateStatement)
        print('[dbUpdateRecordOnTable] %s' % ','.join(
            '%s' % iv
            for iv in updateValues
        ))
    db.execute(updateStatement, updateValues)
    #
    return


def dbOpenDatabase(dbFileName, dbTablesDesc=None, enableForeignKeys=True):
    """Creates an open connection to a database given its filename."""
    con = lite.connect(dbFileName, detect_types=lite.PARSE_DECLTYPES)
    con.execute('PRAGMA foreign_keys = %s;' % (
        ['OFF', 'ON'][int(enableForeignKeys)]
    ))
    return con


def dbDeleteTable(db, tableName, dbTablesDesc=None):
    """ DROP a table. Caution: no questions are asked."""
    deleteCommand = 'DROP TABLE %s;' % tableName
    if DB_DEBUG:
        print('[dbDeleteTable] %s' % deleteCommand)
    cur = db.cursor()
    cur.execute(deleteCommand)


def dbCreateTable(db, tableName, tableDesc, dbTablesDesc=None):
    """ Create a table:
            tableName is a string
            tableDesc can contain a 'primary_key'
                -> nonempty array of pairs  (name,type)
            and holds a 'columns'
                -> similar array with other (name,type) items.
    """
    fieldLines = [
        '%s %s' % fPair
        for fPair in (
            list(tableDesc.get('primary_key', []))
            + list(tableDesc['columns'])
        )
    ]
    #
    if 'primary_key' in tableDesc:
        pkFieldLines = [
            'PRIMARY KEY (%s)' % (
                ', '.join(map(itemgetter(0), tableDesc['primary_key']))
            )
        ]
    else:
        pkFieldLines = []
    if 'foreign_keys' in tableDesc:
        fkFieldLines = [
            'FOREIGN KEY(%s) REFERENCES %s(%s)' % (
                ','.join(fkInfo[0]),
                tbName,
                ','.join(fkInfo[1]),
            )
            for tbName, fkInfoList in tableDesc['foreign_keys'].items()
            for fkInfo in fkInfoList
        ]
    else:
        fkFieldLines = []
    #
    createCommand = 'CREATE TABLE %s (\n\t%s\n);' % (
        tableName,
        ',\n\t'.join(
            fieldLines + pkFieldLines + fkFieldLines
        )
    )
    if DB_DEBUG:
        print('[dbCreateTable] %s' % createCommand)
    cur = db.cursor()
    cur.execute(createCommand)
    # if one or more indices are specified, create them
    if 'indices' in tableDesc:
        '''
            Syntax for creating indices in sqlite3:
                CREATE INDEX index_name ON table_name
                (column [ASC/DESC], column [ASC/DESC],...)
        '''
        for indName, indFieldPairs in tableDesc['indices'].items():
            createCommand = 'CREATE INDEX %s ON %s ( %s );' % (
                indName,
                tableName,
                ' , '.join('%s %s' % fPair for fPair in indFieldPairs)
            )
        if DB_DEBUG:
            print('[dbCreateTable] %s' % createCommand)
        cur = db.cursor()
        cur.execute(createCommand)


def dbClearTable(db, tableName, dbTablesDesc=None):
    """Truncate a table, removing all records. Caution: no questions asked."""
    cur = db.cursor()
    deleteStatement = 'DELETE FROM %s' % tableName
    if DB_DEBUG:
        print('[dbClearTable] %s' % deleteStatement)
    cur.execute(deleteStatement)


def dbRetrieveAllRecords(db, tableName, dbTablesDesc=None):
    """ Return an iterator on dicts, one for each item in the table,
        in no particular order.
    """
    cur = db.cursor()
    columnNames = ', '.join(listColumns(tableName, dbTablesDesc))
    selectStatement = 'SELECT %s FROM %s' % (columnNames, tableName)
    if DB_DEBUG:
        print('[dbRetrieveAllRecords] %s' % selectStatement)
    cur.execute(selectStatement)
    for recTuple in cur.fetchall():
        yield dict(zip(listColumns(tableName, dbTablesDesc), recTuple))


def dbRetrieveRecordsByKey(db, tableName, keys,
                           whereClauses=[], dbTablesDesc=None,
                           order=None, offset=None, limit=None):
    """ Fetch records (an iterable, possibly empty) from a table
        according to a certain query.

        'keys' is for instance {'id': '123', 'status': 'm'}

        whereClauses, the non-equals part of the query, is a mixed
        collection of strings or 2-tuples ('... ? ...', value)
        which is properly routed to the parameterisation for the execute call.

        "order", if not None, must be a list of 2-tuples (first ones first)
            [(fieldName, 'ASC'/'DESC'). ...]

        'offset', if present (nonnegative integer), skips the first matches
        'limit', if present (nonnegative integer), limits the max items yielded
    """
    cur = db.cursor()
    if len(keys) > 0:
        _kNames, _kValues = list(zip(*list(keys.items())))
        kNames, kValues = list(_kNames), list(_kValues)
    else:
        kNames, kValues = [], []
    #
    kValues += [wc[1] for wc in whereClauses if isinstance(wc, tuple)]
    fullWhereClauses = [
        '%s=?' % kn
        for kn in kNames
    ] + [
        wc[0] if isinstance(wc, tuple) else wc
        for wc in whereClauses
    ]
    columnList = listColumns(tableName, dbTablesDesc)
    whereClause = ' AND '.join(fullWhereClauses)
    columnNames = ', '.join(columnList)
    #
    if order is None or len(order) == 0:
        orderClause = ''
    else:
        orderClause = ' ORDER BY %s' % (', '.join(
            '%s %s' % (ordPair[0], ordPair[1])
            for ordPair in order
        ))
    # limit/offset part
    # (see https://dev.mysql.com/doc/refman/8.0/en/select.html)
    if limit is None:
        if offset is None:
            limitClause = ''
        else:
            limitClause = ' LIMIT %i, %s' % (offset, veryLargeIntegerName)
    else:
        if offset is None:
            limitClause = ' LIMIT %i' % limit
        else:
            limitClause = ' LIMIT %i, %i' % (
                offset,
                limit,
            )
    #
    selectStatement = 'SELECT %s FROM %s WHERE %s%s%s' % (
        columnNames,
        tableName,
        whereClause,
        orderClause,
        limitClause,
    )
    if DB_DEBUG:
        print('[dbRetrieveRecordsByKey] %s' % selectStatement)
        print('[dbRetrieveRecordsByKey] %s' % ','.join(
            '%s' % iv
            for iv in kValues
        ))
    cur.execute(selectStatement, kValues)
    docTupleList = cur.fetchall()
    if docTupleList is not None:
        return (
            dict(zip(columnList, docT))
            for docT in docTupleList
        )
    else:
        return None


def dbCountRecordsByKey(db, tableName, keys,
                        whereClauses=[], dbTablesDesc=None):
    """ Count records on a table according to a certain query.

        'keys' and 'whereClauses' params are same as dbRetrieveRecordsByKey

        Return a (nonnegative) integer.
    """
    cur = db.cursor()
    if len(keys) > 0:
        _kNames, _kValues = list(zip(*list(keys.items())))
        kNames, kValues = list(_kNames), list(_kValues)
    else:
        kNames, kValues = [], []
    #
    kValues += [wc[1] for wc in whereClauses if isinstance(wc, tuple)]
    fullWhereClauses = [
        '%s=?' % kn
        for kn in kNames
    ] + [
        wc[0] if isinstance(wc, tuple) else wc
        for wc in whereClauses
    ]
    whereClause = ' AND '.join(fullWhereClauses)
    #
    countStatement = 'SELECT COUNT(*) FROM %s WHERE %s' % (
        tableName,
        whereClause,
    )
    if DB_DEBUG:
        print('[dbCountRecordsByKey] %s' % countStatement)
        print('[dbCountRecordsByKey] %s' % ','.join(
            '%s' % iv
            for iv in kValues
        ))
    cur.execute(countStatement, kValues)
    docTupleList = list(cur.fetchall())
    if len(docTupleList) > 0:
        return docTupleList[0][0]
    else:
        return None


def dbTableExists(db, tableName):
    """ Check for the existence of a table.

        It is assumed that the table is described in the 'sqlite_master' table
        (as opposed to, say, the 'sqlite_temp_master' table for TEMP tables).
    """
    checkerQuery = ("SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name=?;")
    cur = db.cursor()
    items = list(cur.execute(checkerQuery, (tableName,)))
    foundTables = {resItem[0] for resItem in items}
    return tableName in foundTables


def dbRetrieveRecordByKey(db, tableName, key, dbTablesDesc=None):
    """ Fetch a record (or None) according to an equals-only query,
        expressed as a 'key' such as:
            {'id': '123'}
        (describing usually the primary key of the table.
        Returns the row found, if any, as a dict.
    """
    cur = db.cursor()
    kNames, kValues = zip(*list(key.items()))
    whereClause = ' AND '.join('%s=?' % kn for kn in kNames)
    columnNames = ', '.join(listColumns(tableName, dbTablesDesc))
    selectStatement = 'SELECT %s FROM %s WHERE %s' % (
        columnNames,
        tableName,
        whereClause,
    )
    if DB_DEBUG:
        print('[dbRetrieveRecordByKey] %s' % selectStatement)
        print('[dbRetrieveRecordByKey] %s' % ','.join(
            '%s' % iv
            for iv in kValues
        ))
    cur.execute(selectStatement, kValues)
    docTuple = cur.fetchone()
    if docTuple is not None:
        docDict = dict(zip(
            listColumns(tableName, dbTablesDesc=dbTablesDesc),
            docTuple
        ))
        return docDict
    else:
        return None


def dbDeleteRecordsByKey(db, tableName, key, dbTablesDesc=None):
    """ DELETE one or more records from a table according to a
        'key' specification (an equals-only query).
    """
    cur = db.cursor()
    kNames, kValues = zip(*list(key.items()))
    whereClause = ' AND '.join('%s=?' % kn for kn in kNames)
    deleteStatement = 'DELETE FROM %s WHERE %s' % (tableName, whereClause)
    if DB_DEBUG:
        print('[dbDeleteRecordsByKey] %s' % deleteStatement)
        print('[dbDeleteRecordsByKey] %s' % ','.join(
            '%s' % iv
            for iv in kValues
        ))
    cur.execute(deleteStatement, kValues)
