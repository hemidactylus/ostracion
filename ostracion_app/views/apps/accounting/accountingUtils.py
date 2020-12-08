""" accountingUtils.py: utilities behind the accounting app. """

from ostracion_app.views.apps.accounting.db.accountingTools import (
    dbGetLedger,
)

def isLedgerId(db, user, ledgerId):
    return dbGetLedger(db, user, ledgerId) is not None
