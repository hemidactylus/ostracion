""" loginProtection.py
    Handling of the anti-brute-force logic
    to protect logins.
"""

import datetime
import hashlib

from ostracion_app.utilities.models.AttemptedLogin import AttemptedLogin

from ostracion_app.utilities.database.sqliteEngine import (
    dbRetrieveAllRecords,
    dbRetrieveRecordByKey,
    dbAddRecordToTable,
    dbUpdateRecordOnTable,
)

from ostracion_app.utilities.database.dbSchema import (
    dbSchema,
)


def hashOfIpAddress(ipAddr, hashSalt):
    """ Make an IP address into a hashed string."""
    return hashlib.md5(('%s_%s' % (ipAddr, hashSalt)).encode()).hexdigest()


def secondsToWaitBeforeLogin(
        db, ipAddress, doWrite,
        loginProtectionSeconds, hashSalt, skipCommit=False):
    """ Check at once if the record exists
        and if the login is attemptable.
        Moreover update/insert the attempted-login entry in all cases
        and finally (optionally) commit.
    """
    #
    atLogin = AttemptedLogin(
        sender_hash=hashOfIpAddress(ipAddress, hashSalt=hashSalt),
        datetime=datetime.datetime.now(),
    )
    #
    prevLoginDict = dbRetrieveRecordByKey(
        db,
        'attempted_logins',
        {'sender_hash': atLogin.sender_hash},
        dbTablesDesc=dbSchema,
    )
    if prevLoginDict is not None:
        prevLogin = AttemptedLogin(**prevLoginDict)
    else:
        prevLogin = None
    #
    if (
            prevLogin is None or
            (
                datetime.datetime.now()-prevLogin.datetime
            ).seconds >= loginProtectionSeconds):
        secondsToWait = 0
    else:
        secondsToWait = loginProtectionSeconds - (
            datetime.datetime.now()-prevLogin.datetime
        ).seconds
    #
    if doWrite and secondsToWait <= 0:
        if prevLogin is None:
            dbAddRecordToTable(
                db,
                'attempted_logins',
                atLogin.asDict(),
                dbTablesDesc=dbSchema,
            )
        else:
            dbUpdateRecordOnTable(
                db,
                'attempted_logins',
                atLogin.asDict(),
                dbTablesDesc=dbSchema,
            )
        if not skipCommit:
            db.commit()
    #
    return secondsToWait


def getAttemptedLogins(db):
    """ Retrieve and return all attempted logins collected.
        Caution: may become heavy as time goes by (unless
        some cleanup or restricted query logic is introduced).
    """
    return (
        AttemptedLogin(**atDict)
        for atDict in dbRetrieveAllRecords(
            db,
            'attempted_logins',
            dbTablesDesc=dbSchema,
        )
    )
