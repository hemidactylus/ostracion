"""
    calendarmaker.py
"""

import datetime
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

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.views.apps.calendar_maker.forms import CalendarMakerPropertyForm

from ostracion_app.utilities.viewTools.messageTools import flashMessage

from ostracion_app.utilities.tools.extraction import safeInt
from ostracion_app.utilities.tools.formatting import applyDefault

from ostracion_app.utilities.database.fileSystem import (
    getBoxFromPath,
    pathToFileStructure,
    getFilesFromBox,
    getFileFromParent,
    getRootBox,
    splitPathString,
)

from ostracion_app.utilities.database.permissions import (
    userHasPermission,
)

# from ostracion_app.utilities.tools.extraction import safeNone

from ostracion_app.utilities.viewTools.pathTools import (
    describeBoxName,
)
#     makeBreadCrumbs,
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

from ostracion_app.views.apps.utilities import (
    preparePickBoxPage,
)

from ostracion_app.views.apps.calendar_maker.engine.dateTools import (
    countMonths,
)

from ostracion_app.views.apps.calendar_maker.engine.engine import (
    describeSettings,
    defaultCalendarProperties,
)

from ostracion_app.app_main import app

from ostracion_app.views.apps.calendar_maker.engine.settings import (
    admittedImageMimeTypes,
)


def cookiesToCurrentCalendar(cookies):
    cpCookie = cookies.get('apps_calendarmaker_current')
    if cpCookie is None:
        calFromCookie = {}
    else:
        calFromCookie = json.loads(cpCookie)
    # defaults
    defaultCal = {
        'properties': defaultCalendarProperties()
    }
    #
    return recursivelyMergeDictionaries(
        calFromCookie,
        defaultMap=defaultCal,
    )


def dressResponseWithCurrentCalendar(response, cp):
    response.set_cookie(
        'apps_calendarmaker_current',
        json.dumps(cp),
    )
    return response


def applyReindexingToImages(idxMap):
    response = redirect(url_for('calendarMakerImagesView'))
    currentCalendar = cookiesToCurrentCalendar(request.cookies)
    prevImages = currentCalendar.get('image_path_strings', [])
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
            {'image_path_strings': images},
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
    destBoxString = request.cookies.get('apps_calendarmaker_destbox')
    currentCalendar = cookiesToCurrentCalendar(request.cookies)
    coverImagePathString = currentCalendar.get('cover_image_path_string')
    calendarImagePaths = currentCalendar.get('image_path_strings', [])
    cProps = currentCalendar.get('properties', {})
    #
    if destBoxString is None:
        destBoxMessage = 'Destination box not set.'
        destBox = None
        destBoxName = None
    else:
        destBoxMessage = 'Destination box: "%s".' % destBoxString
        destBoxPath = splitPathString(destBoxString)
        destBox = getBoxFromPath(db, destBoxPath, user)
        destBoxName = describeBoxName(destBox)
    if coverImagePathString is None:
        coverMessage = 'Please select a cover'
        coverImageFileObject = None
    else:
        coverMessage = 'Cover selected'
        coverImageFileObject = pathToFileStructure(db, user, coverImagePathString)
    #
    calendarImages = [
        pathToFileStructure(db, user, imgPath)
        for imgPath in calendarImagePaths
    ]
    #
    numRequiredImages = countMonths(
        cProps.get('year0'),
        cProps.get('month0'),
        cProps.get('year1'),
        cProps.get('month1'),
    )
    #
    settingsDesc = describeSettings(cProps)
    settingsSummaryText = (
        'Not set'
        if settingsDesc is None
        else ' '.join('%s.' % stc for stc in settingsDesc)
    )
    #
    if numRequiredImages is not None:
        if numRequiredImages <= len(calendarImages):
            gen1 = True
            gen1Message = []
        else:
            gen1 = False
            gen1Message = ['Select enough images']
    else:
        gen1 = False
        gen1Message = ['Set valid start/end dates']
    if destBox is not None:
        gen2 = True
        gen2Message = []
    else:
        gen2 = False
        gen2Message = ['Select a destination box']
    if coverImageFileObject is not None:
        gen3 = True
        gen3Message = []
    else:
        gen3 = False
        gen3Message = ['Select a cover image']
    canGenerate = all([gen3, gen1, gen2])
    generationMessages = gen3Message + gen1Message + gen2Message
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
        settingsText=settingsSummaryText,
        destBox=destBox,
        destBoxName=destBoxName,
        bgcolor='#90B080',
        calendarImages=calendarImages,
        coverImageFileObject=coverImageFileObject,
        numRequiredImages=numRequiredImages,
        canGenerate=canGenerate,
        generationMessages=generationMessages,
    )

@app.route('/apps/calendarmaker/resetsettings')
def calendarMakerResetSettingsView():
    currentCalendar = cookiesToCurrentCalendar(request.cookies)
    response = redirect(url_for('calendarMakerIndexView'))
    dResponse = dressResponseWithCurrentCalendar(
        response,
        recursivelyMergeDictionaries(
            {
                'properties': defaultCalendarProperties(),
            },
            defaultMap=currentCalendar,
        ),
    )
    return dResponse


@app.route('/apps/calendarmaker/settings', methods=['GET', 'POST'])
def calendarMakerSettingsView():
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'calendarMakerIndexView',
    )
    #
    currentCalendar = cookiesToCurrentCalendar(request.cookies)
    cProps = currentCalendar.get('properties', {})
    currentYear = datetime.datetime.now().year
    form = CalendarMakerPropertyForm()
    #
    if form.validate_on_submit():
        month0 = safeInt(form.month0.data, 1)
        year0 = form.year0.data
        month1 = safeInt(form.month1.data, 12)
        year1 = form.year1.data
        language = form.language.data
        startingweekday = form.startingweekday.data
        response = redirect(url_for('calendarMakerIndexView'))
        dResponse = dressResponseWithCurrentCalendar(
            response,
            recursivelyMergeDictionaries(
                {
                    'properties': {
                        'month0': month0,
                        'year0': year0,
                        'month1': month1,
                        'year1': year1,
                        'language': language,
                        'startingweekday': startingweekday,
                    },
                },
                defaultMap=currentCalendar,
            ),
        )
        return dResponse
    else:
        breadCrumbs = [
            {
                'name': 'Root',
                'type': 'box',
                'target': url_for('lsView'),
                'link': True,
                'is_root_as_pic': True,
            }
        ]
        #
        form.month0.data = str(applyDefault(cProps.get('month0'), 1))
        form.year0.data = applyDefault(cProps.get('year0'), currentYear)
        form.month1.data = str(applyDefault(cProps.get('month1'), 12))
        form.year1.data = applyDefault(cProps.get('year1'), currentYear)
        form.language.data = applyDefault(cProps.get('language'), 'en')
        form.startingweekday.data = applyDefault(
            cProps.get('startingweekday'),
            '6',
        )
        #
        return render_template(
            'apps/calendarmaker/settings.html',
            user=user,
            breadCrumbs=breadCrumbs,
            iconUrl=None,
            pageTitle='SettTitle',
            pageSubtitle='settSubt',
            tasks=None,
            #
            bgcolor='#90B080',
            form=form,
        )


@app.route('/apps/calendarmaker/browsebox/<mode>')
def calendarMakerBrowseBoxView(mode):
    """
        TO DOC
    """
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'calendarMakerImagesView',
    )
    if mode == 'start':
        rootBox = getRootBox(db)
        return preparePickBoxPage(
            db=db,
            user=user,
            callbackUrl=url_for('calendarMakerBrowseBoxView', mode='end'),
            startBox=rootBox,
            message='Choose browsing box',
        )
    elif mode == 'end':
        chosenBoxObjPathBlob = request.args.get('chosenBoxObjPath')
        chosenBoxObjPath = urllib.parse.unquote_plus(chosenBoxObjPathBlob)
        response = redirect(url_for('calendarMakerImagesView'))
        response.set_cookie('apps_calendarmaker_browsebox', chosenBoxObjPath)
        return response
    elif mode == 'clear':
        response = redirect(url_for('calendarMakerImagesView'))
        response.set_cookie('apps_calendarmaker_browsebox', '', expires=0)
        return response
    else:
        raise OstracionError('Malformed request')


@app.route('/apps/calendarmaker/destbox/<mode>')
def calendarMakerDestBoxView(mode):
    """
        TO DOC
    """
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'calendarMakerIndexView',
    )
    rootBox = getRootBox(db)
    if mode == 'start':

        def writableRichBoxPicker(rBox):
            return userHasPermission(db, user, rBox['box'].permissions, 'w')

        return preparePickBoxPage(
            db=db,
            user=user,
            callbackUrl=url_for('calendarMakerDestBoxView', mode='end'),
            startBox=rootBox,
            predicate=writableRichBoxPicker,
            message='Choose destination box',
        )
    elif mode == 'end':
        chosenBoxObjPathBlob = request.args.get('chosenBoxObjPath')
        chosenBoxObjPath = urllib.parse.unquote_plus(chosenBoxObjPathBlob)
        response = redirect(url_for('calendarMakerIndexView'))
        response.set_cookie('apps_calendarmaker_destbox', chosenBoxObjPath)
        return response
    elif mode == 'clear':
        response = redirect(url_for('calendarMakerIndexView'))
        response.set_cookie('apps_calendarmaker_destbox', '', expires=0)
        return response
    else:
        raise OstracionError('Malformed request')


@app.route('/apps/calendarmaker/setcover/<coverObjPath>')
def calendarMakerSetCover(coverObjPath):
    """
        TO DOC
    """
    request._onErrorUrl = url_for(
        'calendarMakerImagesView',
    )
    coverImagePath = urllib.parse.unquote_plus(coverObjPath)
    response = redirect(url_for('calendarMakerImagesView'))
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
    request._onErrorUrl = url_for(
        'calendarMakerImagesView',
    )
    response = redirect(url_for('calendarMakerImagesView'))
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


@app.route('/apps/calendarmaker/unsetimages')
def calendarMakerUnsetImagesView():
    """
        TO DOC
    """
    request._onErrorUrl = url_for(
        'calendarMakerIndexView',
    )
    response = redirect(url_for('calendarMakerIndexView'))
    currentCalendar = cookiesToCurrentCalendar(request.cookies)
    dResponse = dressResponseWithCurrentCalendar(
        response,
        {
            k: v
            for k, v in currentCalendar.items()
            if k != 'cover_image_path_string'
            if k != 'image_path_strings'
        }
    )
    return dResponse


@app.route('/apps/calendarmaker/images')
def calendarMakerImagesView():
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'calendarMakerIndexView',
        lsPathString='',
    )
    #
    browseBoxString = request.cookies.get('apps_calendarmaker_browsebox')
    currentCalendar = cookiesToCurrentCalendar(request.cookies)
    coverImagePathString = currentCalendar.get('cover_image_path_string')
    calendarImagePaths = currentCalendar.get('image_path_strings', [])
    cProps = currentCalendar.get('properties', {})
    #
    if coverImagePathString is None:
        coverImageFileObject = None
    else:
        coverImageFileObject = pathToFileStructure(db, user, coverImagePathString)
    #
    if browseBoxString is not None:
        browseBoxPath = splitPathString(browseBoxString)
        browseBox = getBoxFromPath(db, browseBoxPath, user)
        choosableFiles = [
            {
                'file': file,
                'path': browseBoxPath[1:] + [file.name],
                'obj_path': urllib.parse.quote_plus('/'.join(
                    browseBoxPath[1:] + [file.name],
                )),
            }
            for file in sorted(
                getFilesFromBox(db, browseBox),
                key=lambda f: (f.name.lower(), f.name),
            )
            if file.mime_type in admittedImageMimeTypes
        ]
        browseBoxName = describeBoxName(browseBox)
    else:
        browseBox = None
        browseBoxName = None
        choosableFiles = []
    #
    calendarImages = [
        pathToFileStructure(db, user, imgPath)
        for imgPath in calendarImagePaths
    ]
    #
    numRequiredImages = countMonths(
        cProps.get('year0'),
        cProps.get('month0'),
        cProps.get('year1'),
        cProps.get('month1'),
    )
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
        'apps/calendarmaker/images.html',
        user=user,
        breadCrumbs=breadCrumbs,
        iconUrl=None,
        pageTitle='imgTitle',
        pageSubtitle='imgSubt',
        tasks=None,
        #
        browseBox=browseBox,
        browseBoxName=browseBoxName,
        choosableFiles=choosableFiles,
        coverImageFileObject=coverImageFileObject,
        bgcolor='#90B080',
        calendarImages=calendarImages,
        numRequiredImages=numRequiredImages,
    )


@app.route('/apps/calendarmaker/addimage/<imageObjPath>')
def calendarMakerAddImage(imageObjPath):
    """
        TO DOC
    """
    request._onErrorUrl = url_for(
        'calendarMakerImagesView',
    )
    imagePath = urllib.parse.unquote_plus(imageObjPath)
    response = redirect(url_for('calendarMakerImagesView'))
    currentCalendar = cookiesToCurrentCalendar(request.cookies)
    images = currentCalendar.get('image_path_strings', []) + [imagePath]
    dResponse = dressResponseWithCurrentCalendar(
        response,
        recursivelyMergeDictionaries(
            {'image_path_strings': images},
            defaultMap=currentCalendar,
        ),
    )
    return dResponse


@app.route('/apps/calendarmaker/removeimage/<int:index>')
def calendarMakerRemoveImage(index):
    """
        TO DOC
    """
    request._onErrorUrl = url_for(
        'calendarMakerImagesView',
    )
    return applyReindexingToImages({index: None})


@app.route('/apps/calendarmaker/swapimages/<int:index1>/<int:index2>')
def calendarMakerSwapImages(index1, index2):
    """
        TO DOC
    """
    request._onErrorUrl = url_for(
        'calendarMakerImagesView',
    )
    return applyReindexingToImages({
        index1: index2,
        index2: index1,
    })
