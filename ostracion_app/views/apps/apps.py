"""
    apps.py
"""

from flask import (
    redirect,
    url_for,
    render_template,
    request,
    g,
)

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)

from ostracion_app.utilities.viewTools.pathTools import (
    prepareTaskPageFeatures,
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
