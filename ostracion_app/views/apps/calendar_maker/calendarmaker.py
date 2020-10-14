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
    getBoxFromPath,
    # makeBoxInParent,
    # updateBox,
    # deleteBox,
    getFilesFromBox,
    # getLinksFromBox,
    getRootBox,
    # isNameUnderParentBox,
    # canDeleteBox,
    # isAncestorBoxOf,
    # moveBox,
)

from ostracion_app.utilities.viewTools.pathTools import (
#     makeBreadCrumbs,
    splitPathString,
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
)

from ostracion_app.views.apps.utilities import preparePickBoxPage

from ostracion_app.app_main import app

@app.route('/apps/calendarmaker/')
@app.route('/apps/calendarmaker/index')
def calendarMakerIndexView():
    """
        TO DOC
    """
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='',
    )
    #
    pickedDir = request.cookies.get('apps_calendarmaker_pickeddir')
    if pickedDir is None:
        message = 'Please pick a box'
    else:
        message = 'Picked box: "%s"' % pickedDir
    #
    if pickedDir is not None:
        boxPath = splitPathString(pickedDir)
        thisBox = getBoxFromPath(db, boxPath, user)
        choosableFiles = [
            {
                'file': file,
                'path': boxPath[1:] + [file.name],
                'obj_path': urllib.parse.quote_plus('/'.join(
                    boxPath[1:] + [file.name],
                )),
                # 'nice_size': formatBytesSize(file.size),
                # 'info': prepareFileInfo(db, file),
                # 'actions': prepareFileActions(
                #     db,
                #     file,
                #     boxPath + [file.name],
                #     thisBox,
                #     user
                # ),
            }
            for file in sorted(
                getFilesFromBox(db, thisBox),
                key=lambda f: (f.name.lower(), f.name),
            )
        ]
    else:
        choosableFiles = []
    #
    breadCrumbs = [
        {
            'name': 'Root',
            'type': 'box',
            'target': url_for('lsView'),
            'link': True,
            'is_root_as_pic': True,
        }
    ]
    return render_template(
        'apps/calendarmaker/index.html',
        user=user,
        breadCrumbs=breadCrumbs,
        iconUrl=None,
        pageTitle='Title',
        pageSubtitle='subt',
        tasks=None,
        #
        message=message,
        choosableFiles=choosableFiles,
    )


@app.route('/apps/calendarmaker/pickbox_s')
def calendarMakerPickBoxStartView():
    """
        TO DOC
    """
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'calendarMakerIndexView',
        lsPathString='',
    )
    rootBox = getRootBox(db)
    return preparePickBoxPage(
        db=db,
        user=user,
        callbackUrl=url_for('calendarMakerPickBoxEndView'),
        startBox=rootBox,
    )


@app.route('/apps/calendarmaker/pickbox_e')
def calendarMakerPickBoxEndView():
    """
        TO DOC
    """
    chosenBoxObjPathBlob = request.args.get('chosenBoxObjPath')
    chosenBoxObjPath = urllib.parse.unquote_plus(chosenBoxObjPathBlob)
    response = redirect(url_for('calendarMakerIndexView'))
    response.set_cookie('apps_calendarmaker_pickeddir', chosenBoxObjPath)
    return response


@app.route('/apps/calendarmaker/unpickbox')
def calendarMakerUnpickBoxView():
    """
        TO DOC
    """
    response = redirect(url_for('calendarMakerIndexView'))
    response.set_cookie('apps_calendarmaker_pickeddir', '', expires=0)
    return response
