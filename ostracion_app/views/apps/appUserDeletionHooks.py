"""
    appUserDeletionHooks.py
"""

from ostracion_app.views.apps.accounting.userDeletion import (
    accountingUserDeletion,
)


userDeletionHookMap = {
    'accounting': accountingUserDeletion,
}
