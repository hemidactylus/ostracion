""" accountingUtils.py: utilities behind the accounting app. """

from flask import url_for

from ostracion_app.views.apps.appsPageTreeDescriptor import appsPageDescriptor

from ostracion_app.utilities.viewTools.pathTools import (
    prepareTaskPageFeatures,
)

from ostracion_app.utilities.database.userTools import (
    getUserFullName,
)

from ostracion_app.utilities.database.permissions import (
    userHasRole,
    userIsAdmin,
)

from ostracion_app.views.apps.accounting.db.accountingTools import (
    dbGetLedger,
    dbGetCategoriesForLedger,
    dbGetSubcategoriesForLedger,
    dbGetUsersForLedger,
    dbGetActorsForLedger,
)


def isLedgerId(db, user, ledgerId):
    """
        Check if the ledgerId corresponds to a ledger
        and return True in that case.
    """
    return dbGetLedger(db, user, ledgerId) is not None


def extractLedgerCategoryTree(db, user, ledger):
    """
        Extract, for a given ledger, the tree
            categories -> subcategories
        and cast it as a tree suitable for rendering.
    """
    return sorted(
        [
            {
                'category': cat,
                'subcategories': sorted(
                    [
                        subcat
                        for subcat in dbGetSubcategoriesForLedger(
                            db,
                            user,
                            ledger,
                            cat,
                        )
                    ],
                    key=lambda subcat: subcat.sort_index,
                )
            }
            for cat in dbGetCategoriesForLedger(db, user, ledger)
        ],
        key=lambda cObj: cObj['category'].sort_index,
    )


def prepareAccountingCategoryViewFeatures(g, ledgerId):
    """
        Factored-away preparation of features for the "ledger categories"
        admin-only page.
    """
    pageFeatures = prepareTaskPageFeatures(
        appsPageDescriptor,
        ['root', 'accounting'],
        g,
        overrides={
            'pageTitle': 'Categories for ledger "%s"' % ledgerId,
            'pageSubtitle': ('Configure categorisation of ledger movements. '
                             'Use the "+" buttons to add new categories/subc'
                             'ategories, and the buttons on each row to '
                             'delete/move the item.'),
        },
        appendedItems=[{
            'kind': 'link',
            'target': None,
            'name': 'Categories for ledger',
        }],
    )
    return pageFeatures


def prepareLedgerActions(db, user, ledger):
    """
        Prepare the ledger-specific actions for display in cards.
    """
    lActions = {}
    #
    if userHasRole(db, user, 'app', 'accounting') or userIsAdmin(db, user):
        if userIsAdmin(db, user):
            lActions['metadata'] = url_for(
                'accountingEditLedgerView',
                ledgerId=ledger.ledger_id,
            )
            lActions['app_accounting_users'] = url_for(
                'accountingLedgerUsersView',
                ledgerId=ledger.ledger_id,
            )
            lActions['app_accounting_actors'] = url_for(
                'accountingLedgerActorsView',
                ledgerId=ledger.ledger_id,
            )
            lActions['app_accounting_categories'] = url_for(
                'accountingLedgerCategoriesView',
                ledgerId=ledger.ledger_id,
            )
            lActions['delete'] = url_for(
                'accountingDeleteLedgerView',
                ledgerId=ledger.ledger_id,
            )
            lActions['icon'] = url_for(
                'setIconView',
                mode='accounting_ledger',
                itemPathString=ledger.ledger_id,
            )
    #
    return lActions


def prepareLedgerSummary(db, user, ledger):
    """Calculate a text summary of a ledger."""
    namedFields = ['ledger_id', 'name', 'description', 'creator_username',
                   'creation_date',  'configuration_date', 'last_edit_date',
                   'last_edit_username', 'icon_file_id',
                   'icon_file_id_username', 'icon_mime_type']
    numActors = len(list(dbGetActorsForLedger(db, user, ledger)))
    lastEditDate = ledger.last_edit_date
    return '%i actor%s. Last edited: %s' % (
        numActors,
        '' if numActors == 1 else 's',
        lastEditDate.strftime(' %b %d %H:%M'),
    )


def prepareLedgerInfo(db, user, ledger):
    """Calculate ledger information for display."""
    return [
        infoItem
        for infoItem in (
            {
                'action': 'Created',
                'actor': getUserFullName(db, ledger.creator_username),
            },
            {
                'action': 'Last edited',
                'actor': (getUserFullName(db, ledger.last_edit_username)
                          if (ledger.creator_username
                              != ledger.last_edit_username)
                          else None),
            },
            # {
            #     'action': 'Icon',
            #     'actor': getUserFullName(db, ledger.icon_file_id_username),
            # },
        )
        if infoItem['actor'] is not None
    ]
