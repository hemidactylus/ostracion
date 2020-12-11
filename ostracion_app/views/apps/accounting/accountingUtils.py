""" accountingUtils.py: utilities behind the accounting app. """

from ostracion_app.views.apps.appsPageTreeDescriptor import appsPageDescriptor

from ostracion_app.utilities.viewTools.pathTools import (
    prepareTaskPageFeatures,
)

from ostracion_app.views.apps.accounting.db.accountingTools import (
    dbGetLedger,
    dbGetCategoriesForLedger,
    dbGetSubcategoriesForLedger
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
