"""
    appRegisteredPlugins.py
        Minimal-coupling set of definitions to handle flows
        for app-related items, such as: set-icon flows.
"""

from ostracion_app.views.apps.accounting.accountingThumbnails import (
    accountingItemer,
    accountingItemNamer,
    accountingPageFeaturer,
    thumbnailModeDeterminer,
    updateLedgerThumbnail,
    endOfFlowPager,
)


appsSetIconModes = {
    'accounting_ledger': {
        'extractors': {
            'thisItemer': accountingItemer,
            'itemNamer': accountingItemNamer,
            'pageFeaturer': accountingPageFeaturer,
            'thumbnailModer': thumbnailModeDeterminer,
        },
        'texts': {
            'formTitle': 'Set Ledger Icon',
            'formModeName': 'for ledger',
        },
        'changers': {
            'thumbnailUpdater': updateLedgerThumbnail,
        },
        'pages': {
            'endOfFlowPager': endOfFlowPager,
        },
    },
}
