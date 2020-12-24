"""
    accountingThumbnails.py
        Tools to handle thumbnail handling
        (embedded in the regular thumbnail-changing flow)
"""

from flask import (
    url_for,
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.fileIO.physical import (
    fileIdToPath,
)

from ostracion_app.views.apps.appsPageTreeDescriptor import appsPageDescriptor

from ostracion_app.utilities.viewTools.pathTools import (
    prepareTaskPageFeatures,
)

from ostracion_app.views.apps.accounting.db.accountingTools import (
    dbGetLedger,
    dbUpdateLedger,
)

from ostracion_app.utilities.database.permissions import (
    userIsAdmin,
)


def accountingItemer(db, g, user, itemPathString):
    """Prepare the 'item' for the change-thumbnail general flow."""
    if userIsAdmin(db, user):
        ledger = dbGetLedger(db, user, itemPathString)
        if ledger is not None:
            return ledger
        else:
            raise OstracionError('Unknown ledger')
    else:
        raise OstracionError('Insufficient permission')


def accountingItemNamer(db, g, user, item, itemPathString):
    """Prepare the 'item name' for the change-thumbnail general flow."""
    return item.name


def accountingPageFeaturer(db, g, user, item, itemPathString):
    """Prepare a 'pageFeatures' object for the set-icon view."""
    pageFeatures = prepareTaskPageFeatures(
        appsPageDescriptor,
        ['root', 'accounting'],
        g,
        appendedItems=[
            {
                'kind': 'link',
                'link': False,
                'target': url_for(
                    'setIconView',
                    mode='accounting_ledger',
                    itemPathString=item.ledger_id,
                ),
                'name': 'Set image',
            }
        ],
        overrides={
            'pageTitle': None,
            'pageSubtitle': None,
            'iconUrl': url_for(
                'appItemThumbnailView',
                mode='accounting_ledger',
                dummyId=item.icon_file_id+'_',
                itemId=item.ledger_id,
            ),
        }
    )
    return pageFeatures


def thumbnailModeDeterminer(db, target):
    return 'thumbnail'


def updateLedgerThumbnail(
        db, ledger, tId, tMT, user, fileStorageDirectory,
        accountDeletionInProgress=False, skipCommit=False):
    """ Update the thumbnail info for a ledger.
        Return a list of zero or one full paths for deletion."""
    prevId = ledger.icon_file_id
    if prevId != '':
        delQueue = [
            fileIdToPath(prevId, fileStorageDirectory=fileStorageDirectory)
        ]
    else:
        delQueue = []
    #
    ledger.icon_file_id = tId if tId is not None else ''
    ledger.icon_mime_type = tMT if tMT is not None else ''
    ledger.icon_file_id_username = (user.username
                                    if not accountDeletionInProgress
                                    else '')
    dbUpdateLedger(
        db,
        user,
        ledger,
        skipCommit=skipCommit,
    )
    #
    return delQueue


def endOfFlowPager(db, user, item):
    """Return the URL to redirect the user after the icon has been changed."""
    return url_for('accountingIndexView')
