"""
    accounting.py
        An app to manage ledgers of debts/credits among arbitrary actors
"""

# import os
# from uuid import uuid4
# import datetime
# import urllib.parse
from flask import (
    redirect,
    url_for,
    render_template,
    request,
    send_from_directory,
    g,
)

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)

# from ostracion_app.utilities.tools.dictTools import (
#     recursivelyMergeDictionaries
# )

# from ostracion_app.utilities.exceptions.exceptions import (
#     OstracionWarning,
#     OstracionError,
# )

# from ostracion_app.utilities.viewTools.messageTools import flashMessage

# from ostracion_app.utilities.tools.extraction import safeInt
# from ostracion_app.utilities.tools.formatting import applyDefault

# from ostracion_app.utilities.database.fileSystem import (
#     getBoxFromPath,
#     pathToFileStructure,
#     getFilesFromBox,
#     getFileFromParent,
#     findFirstAvailableObjectNameInBox,
#     getRootBox,
#     splitPathString,
# )

# from ostracion_app.utilities.database.permissions import (
#     userHasPermission,
# )

# from ostracion_app.utilities.viewTools.pathTools import (
#     describeBoxName,
# )

# from ostracion_app.views.apps.utilities import (
#     preparePickBoxPageView,
#     placeFSFileInBox,
# )

from ostracion_app.views.apps.appsPageTreeDescriptor import appsPageDescriptor

from ostracion_app.utilities.viewTools.pathTools import (
    prepareTaskPageFeatures,
)

# from ostracion_app.utilities.fileIO.physical import (
#     fileIdToPath,
#     flushFsDeleteQueue,
#     mkDirP,
# )

from ostracion_app.app_main import app


@app.route('/apps/accounting/')
@app.route('/apps/accounting/index')
def accountingIndexView():
    """Main accounting view."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='',
    )
    #
    pageFeatures = prepareTaskPageFeatures(
        appsPageDescriptor,
        ['root', 'accounting'],
        g,
    )
    #
    return render_template(
        'apps/accounting/index.html',
        user=user,
        bgcolor=g.settings['color']['app_colors'][
            'accounting_main_color']['value'],
        admin_bgcolor=g.settings['color']['app_colors'][
            'accounting_admin_color']['value'],
        **pageFeatures,
    )
