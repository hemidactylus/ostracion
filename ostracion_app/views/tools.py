""" tools.py
    views regrouping 'tools' such as find or tree view.
"""

from ostracion_app.app_main import app

from flask import (
    render_template,
    g,
    send_from_directory,
    abort,
)

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)

from ostracion_app.utilities.viewTools.pathTools import (
    prepareTaskPageFeatures,
)


@app.route('/tools')
def toolsHomeView():
    """Index page for the 'tools' tasks, which are elsewhere in themselves."""
    user = g.user
    db = dbGetDatabase()
    #
    filteredToolsPageDescriptor = g.availableTools
    #
    pageFeatures = prepareTaskPageFeatures(
        filteredToolsPageDescriptor,
        ['root'],
        g,
    )
    return render_template(
        'tasks.html',
        user=user,
        bgcolor=g.settings['color']['task_colors']['tool_task']['value'],
        **pageFeatures,
    )
