""" accountingUtils.py: utilities behind the accounting app. """

from ostracion_app.views.apps.accounting.db.accountingTools import (
    dbGetLedger,
)

def isLedgerId(db, ledgerId, user):
    return dbGetLedger(db, ledgerId) is not None
