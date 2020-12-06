"""
    descriptors.py
        actual construction of the descriptor for navbar menus
        and at the same time task-page elements.
"""

from ostracion_app.utilities.database.permissions import (
    userHasRole,
    userIsAdmin,
)

from ostracion_app.views.viewTools.infoPageTreeDescriptor import (
    infoPageDescriptor,
)
from ostracion_app.views.viewTools.pageTreeDescriptorTools import (
    filterPageDescriptor,
)
from ostracion_app.views.viewTools.toolsPageTreeDescriptor import (
    toolsPageDescriptor,
)
from ostracion_app.views.apps.appsPageTreeDescriptor import appsPageDescriptor


def selectAvailableInfoItems(db, user, gg):
    """
        Return a page descriptor adapted
        to the available "info" pages.
    """
    return filterPageDescriptor(
        infoPageDescriptor,
        subTasksAccessibility={
            'root': {
                'admin_guide':  userIsAdmin(db, user),
            },
        },
    )


def selectAvailableApps(db, user, gg):
    """
        Return a page descriptor adapted to the apps
        available to the provided user.
    """
    return filterPageDescriptor(
        appsPageDescriptor,
        subTasksAccessibility={
            'root': {
                'calendar_maker':  userHasRole(
                    db,
                    user,
                    'app',
                    'calendarmaker'
                ),
                'accounting': userHasRole(
                    db,
                    user,
                    'app',
                    'accounting'
                ) or userIsAdmin(
                    db,
                    user,
                )
            },
        },
    )


def selectAvailableTools(db, user, gg):
    """
        Return a page descriptor adapted
        to the available "tools" pages.
    """
    return filterPageDescriptor(
        toolsPageDescriptor,
        subTasksAccessibility={
            'root': {
                'tree_view': gg.canShowTreeView,
                'search': gg.canPerformSearch,
            },
        },
    )
