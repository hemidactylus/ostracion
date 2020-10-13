"""
    calendarmaker.py
"""

import urllib.parse

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

from ostracion_app.utilities.viewTools.messageTools import flashMessage

from ostracion_app.utilities.database.fileSystem import (
    # getBoxesFromParent,
    # getBoxFromPath,
    # makeBoxInParent,
    # updateBox,
    # deleteBox,
    # getFilesFromBox,
    # getLinksFromBox,
    getRootBox,
    # isNameUnderParentBox,
    # canDeleteBox,
    # isAncestorBoxOf,
    # moveBox,
)

# from ostracion_app.utilities.viewTools.pathTools import (
#     makeBreadCrumbs,
#     splitPathString,
#     prepareBoxActions,
#     prepareFileActions,
#     prepareLinkActions,
#     prepareFileInfo,
#     prepareLinkInfo,
#     prepareBoxInfo,
#     prepareBoxHeaderActions,
#     prepareRootTasks,
#     describeBoxTitle,
#     describeBoxName,
#     describeRootBoxCaptions,
# )

from ostracion_app.views.apps.utilities import preparePickBoxPage

from ostracion_app.app_main import app


@app.route('/apps/calendarmaker/pickdirtest1')
def pickDirTest1View():
    """
        TO DOC
    """
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='',
    )
    rootBox = getRootBox(db)
    return preparePickBoxPage(
        db=db,
        user=user,
        callbackUrl=url_for('pickDirTest2View'),
        startBox=rootBox,
    )


@app.route('/apps/calendarmaker/pickdirtest2')
def pickDirTest2View():
    chosenBoxObjPathBlob = request.args.get('chosenBoxObjPath')
    chosenBoxObjPath = urllib.parse.unquote_plus(chosenBoxObjPathBlob)
    flashMessage(
        'Success',
        'Selection',
        'Chosen box = %s' % chosenBoxObjPath,
    )
    return redirect(url_for('lsView'))
