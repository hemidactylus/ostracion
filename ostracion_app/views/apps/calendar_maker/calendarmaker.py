"""
    calendarmaker.py
"""

import urllib.parse
import json
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

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries
)

from ostracion_app.views.apps.calendar_maker.forms import CalendarMakerPropertyForm

from ostracion_app.utilities.viewTools.messageTools import flashMessage

from ostracion_app.utilities.database.fileSystem import (
    # getBoxesFromParent,
    getBoxFromPath,
    # makeBoxInParent,
    # updateBox,
    # deleteBox,
    getFilesFromBox,
    # getLinksFromBox,
    getFileFromParent,
    getRootBox,
    # isNameUnderParentBox,
    # canDeleteBox,
    # isAncestorBoxOf,
    # moveBox,
)

from ostracion_app.utilities.database.permissions import (
    userHasPermission,
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


admittedImageMimeTypes = {
    'image/gif', 
    'image/jpeg', 
    'image/png', 
}


def cookiesToCurrentCalendar(cookies):
    cpCookie = cookies.get('apps_calendarmaker_current')
    if cpCookie is None:
        return {}
    else:
        curCal = json.loads(cpCookie)
        return curCal


def dressResponseWithCurrentCalendar(response, cp):
    response.set_cookie(
        'apps_calendarmaker_current',
        json.dumps(cp),
    )
    return response


def pathToFileStructure(db, user, fPath):
    fPath = splitPathString(fPath)
    fBoxPath, fFileName = fPath[:-1], fPath[-1]
    fParentBox = getBoxFromPath(db, fBoxPath, user)
    fFile = getFileFromParent(db, fParentBox, fFileName, user)
    #
    fStructure = {
        'path': fPath,
        'file': fFile,
        'parent_box': fParentBox,
    }
    return fStructure

def applyReindexingToImages(idxMap):
    response = redirect(url_for('calendarMakerIndexView'))
    currentCalendar = cookiesToCurrentCalendar(request.cookies)
    prevImages = currentCalendar.get('images', [])
    images = [
        prevImages[idxMap.get(idx, idx)]
        for idx in range(len(prevImages))
        if idxMap.get(idx, idx) is not None
        if idxMap.get(idx, idx) >= 0
        if idxMap.get(idx, idx) < len(prevImages)
    ]
    dResponse = dressResponseWithCurrentCalendar(
        response,
        recursivelyMergeDictionaries(
            {'images': images},
            defaultMap=currentCalendar
        ),
    )
    return dResponse


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
    viewBox = request.cookies.get('apps_calendarmaker_viewbox')
    if viewBox is None:
        viewBoxMessage = 'Please pick a box'
    else:
        viewBoxMessage = 'Picked box: "%s"' % viewBox
    #
    destBox = request.cookies.get('apps_calendarmaker_destbox')
    if destBox is None:
        destBoxMessage = 'Please pick a dest box'
    else:
        destBoxMessage = 'Picked dest box: "%s"' % destBox
    #
    currentCalendar = cookiesToCurrentCalendar(request.cookies)
    coverImagePathString = currentCalendar.get('cover_image_path_string')
    if coverImagePathString is None:
        coverMessage = 'Please select a cover'
        coverImageFileObject = None
    else:
        coverMessage = 'Cover selected'
        coverImageFileObject = pathToFileStructure(db, user, coverImagePathString)
    #
    if viewBox is not None:
        boxPath = splitPathString(viewBox)
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
            if file.mime_type in admittedImageMimeTypes
        ]
    else:
        choosableFiles = []
    #
    calendarImagePaths = currentCalendar.get('images', [])
    calendarImages = [
        pathToFileStructure(db, user, imgPath)
        for imgPath in calendarImagePaths
    ]
    #
    form = CalendarMakerPropertyForm()
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
        viewBoxMessage=viewBoxMessage,
        destBoxMessage=destBoxMessage,
        choosableFiles=choosableFiles,
        coverMessage=coverMessage,
        coverImageFileObject=coverImageFileObject,
        bgcolor='#90B080',
        calendarImages=calendarImages,
        form=form,
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
        message='Please specify the source of all images',
    )


@app.route('/apps/calendarmaker/pickbox_e')
def calendarMakerPickBoxEndView():
    """
        TO DOC
    """
    chosenBoxObjPathBlob = request.args.get('chosenBoxObjPath')
    chosenBoxObjPath = urllib.parse.unquote_plus(chosenBoxObjPathBlob)
    response = redirect(url_for('calendarMakerIndexView'))
    response.set_cookie('apps_calendarmaker_viewbox', chosenBoxObjPath)
    return response


@app.route('/apps/calendarmaker/unpickbox')
def calendarMakerUnpickBoxView():
    """
        TO DOC
    """
    response = redirect(url_for('calendarMakerIndexView'))
    response.set_cookie('apps_calendarmaker_viewbox', '', expires=0)
    return response


@app.route('/apps/calendarmaker/pickdestbox_s')
def calendarMakerPickDestBoxStartView():
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

    def writableRichBoxPicker(rBox):
        return userHasPermission(db, user, rBox['box'].permissions, 'w')

    return preparePickBoxPage(
        db=db,
        user=user,
        callbackUrl=url_for('calendarMakerPickDestBoxEndView'),
        startBox=rootBox,
        predicate=writableRichBoxPicker,
        message='Please choose the box in which the calendar will be created',
    )



@app.route('/apps/calendarmaker/pickdestbox_e')
def calendarMakerPickDestBoxEndView():
    """
        TO DOC
    """
    chosenBoxObjPathBlob = request.args.get('chosenBoxObjPath')
    chosenBoxObjPath = urllib.parse.unquote_plus(chosenBoxObjPathBlob)
    response = redirect(url_for('calendarMakerIndexView'))
    response.set_cookie('apps_calendarmaker_destbox', chosenBoxObjPath)
    return response


@app.route('/apps/calendarmaker/unpickdestbox')
def calendarMakerUnpickDestBoxView():
    """
        TO DOC
    """
    response = redirect(url_for('calendarMakerIndexView'))
    response.set_cookie('c v vbgtfrfcx', '', expires=0)
    return response


@app.route('/apps/calendarmaker/setcover/<coverObjPath>')
def calendarMakerSetCover(coverObjPath):
    """
        TO DOC
    """
    coverImagePath = urllib.parse.unquote_plus(coverObjPath)
    response = redirect(url_for('calendarMakerIndexView'))
    currentCalendar = cookiesToCurrentCalendar(request.cookies)
    dResponse = dressResponseWithCurrentCalendar(
        response,
        recursivelyMergeDictionaries(
            {'cover_image_path_string': coverImagePath},
            defaultMap=currentCalendar
        ),
    )
    return dResponse


@app.route('/apps/calendarmaker/unsetcover')
def calendarMakerUnsetCover():
    """
        TO DOC
    """
    response = redirect(url_for('calendarMakerIndexView'))
    currentCalendar = cookiesToCurrentCalendar(request.cookies)
    dResponse = dressResponseWithCurrentCalendar(
        response,
        {
            k: v
            for k, v in currentCalendar.items()
            if k != 'cover_image_path_string'
        }
    )
    return dResponse

    response = redirect(url_for('calendarMakerIndexView'))
    response.set_cookie('apps_calendarmaker_cover_image_path', '', expires=0)
    return response


@app.route('/apps/calendarmaker/addimage/<imageObjPath>')
def calendarMakerAddImage(imageObjPath):
    """
        TO DOC
    """
    imagePath = urllib.parse.unquote_plus(imageObjPath)
    response = redirect(url_for('calendarMakerIndexView'))
    currentCalendar = cookiesToCurrentCalendar(request.cookies)
    images = currentCalendar.get('images', []) + [imagePath]
    dResponse = dressResponseWithCurrentCalendar(
        response,
        recursivelyMergeDictionaries(
            {'images': images},
            defaultMap=currentCalendar
        ),
    )
    return dResponse


@app.route('/apps/calendarmaker/removeimage/<int:index>')
def calendarMakerRemoveImage(index):
    """
        TO DOC
    """
    return applyReindexingToImages({index: None})


@app.route('/apps/calendarmaker/swapimages/<int:index1>/<int:index2>')
def calendarMakerSwapImages(index1, index2):
    """
        TO DOC
    """
    return applyReindexingToImages({
        index1: index2,
        index2: index1,
    })
