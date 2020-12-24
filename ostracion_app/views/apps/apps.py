"""
    apps.py
"""

from flask import (
    redirect,
    url_for,
    render_template,
    request,
    send_from_directory,
    abort,
    g,
)

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)

from ostracion_app.utilities.fileIO.physical import (
    fileIdToSplitPath,
)

from ostracion_app.utilities.viewTools.pathTools import (
    prepareTaskPageFeatures,
)

from ostracion_app.views.apps.accounting.db.accountingTools import (
    dbGetLedger,
)

from ostracion_app.utilities.database.settingsTools import (
    makeSettingImageUrl,
)

from ostracion_app.app_main import app


@app.route('/apps/')
def appsView():
    """Main apps page with tasks (each an available app)."""
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='',
    )
    #
    filteredAppsPageDescriptor = g.availableApps
    #
    pageFeatures = prepareTaskPageFeatures(
        filteredAppsPageDescriptor,
        ['root'],
        g,
    )
    return render_template(
        'tasks.html',
        user=user,
        bgcolor=g.settings['color']['task_colors']['info_task']['value'],
        **pageFeatures,
    )


@app.route('/apps/thumbnail/<mode>/<dummyId>/<itemId>')
def appItemThumbnailView(mode, dummyId, itemId):
    """
        Route for access to app-item thumbnail image file based on its ID
        (ID in broad sense: for a ledger it is ledger_id, for instance).
    """
    user = g.user
    db = dbGetDatabase()
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    if mode == 'accounting_ledger':
        ledger = dbGetLedger(db, user, itemId)
        if (ledger is not None and
                ledger.icon_file_id is not None and
                ledger.icon_file_id != ''):
            filePhysicalPath, filePhysicalName = fileIdToSplitPath(
                ledger.icon_file_id,
                fileStorageDirectory=fileStorageDirectory,
            )
            return send_from_directory(
                filePhysicalPath,
                filePhysicalName,
                mimetype=ledger.icon_mime_type,
            )
        else:
            return redirect(makeSettingImageUrl(
                g,
                'custom_apps_images',
                'accounting_ledger',
            ))
    else:
        return abort(404, 'Unknown app-thumbnail mode')
