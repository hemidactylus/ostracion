"""
    calendarmaker.py
        An app to handle generation of (pdf) calendars
        from images hosted in Ostracion.
"""

import os
from uuid import uuid4
import datetime
import urllib.parse
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

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.views.apps.calendar_maker.forms import (
    CalendarMakerPropertyForm,
)

from ostracion_app.utilities.viewTools.messageTools import flashMessage

from ostracion_app.utilities.tools.extraction import safeInt
from ostracion_app.utilities.tools.formatting import applyDefault

from ostracion_app.utilities.database.fileSystem import (
    getBoxFromPath,
    pathToFileStructure,
    getFilesFromBox,
    getFileFromParent,
    findFirstAvailableObjectNameInBox,
    getRootBox,
    splitPathString,
)

from ostracion_app.utilities.database.permissions import (
    userHasPermission,
)

from ostracion_app.utilities.viewTools.pathTools import (
    describeBoxName,
)

from ostracion_app.views.apps.utilities import (
    preparePickBoxPageView,
    placeFSFileInBox,
)

from ostracion_app.views.apps.appsPageTreeDescriptor import appsPageDescriptor

from ostracion_app.utilities.viewTools.pathTools import (
    prepareTaskPageFeatures,
)

from ostracion_app.views.apps.calendar_maker.engine.dateTools import (
    countMonths,
)

from ostracion_app.views.apps.calendar_maker.engine.calendarTools import (
    describeSettings,
    defaultCalendarProperties,
)

from ostracion_app.views.apps.calendar_maker.engine.settings import (
    admittedImageMimeTypeToExtension,
)

from ostracion_app.utilities.fileIO.physical import (
    fileIdToPath,
    flushFsDeleteQueue,
    mkDirP,
)

from ostracion_app.views.apps.calendar_maker.engine.calendarEngine import (
    makeCalendarPdf,
    duplicateImageForCalendar,
)

from ostracion_app.views.apps.calendar_maker.calendarViewUtils import (
    cookiesToCurrentCalendar,
    dressResponseWithCurrentCalendar,
    applyReindexingToImages,
)

from ostracion_app.app_main import app


@app.route('/apps/calendarmaker/')
@app.route('/apps/calendarmaker/index')
def calendarMakerIndexView():
    """Main calendar maker view."""
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
        coverImageFileObject = pathToFileStructure(
            db,
            user,
            coverImagePathString,
        )
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
        gen0 = True
        gen3Message = []
    else:
        gen0 = False
        gen3Message = ['Select a cover image']
    canGenerate = all([gen0, gen1, gen2])
    generationMessages = gen3Message + gen1Message + gen2Message
    pageFeatures = prepareTaskPageFeatures(
        appsPageDescriptor,
        ['root', 'calendar_maker'],
        g,
        overrides={
            'pageSubtitle': ('Create your own custom calendar. (1) Configure '
                             'dates and calendar appearance. (2) Select enoug'
                             'h images. (3) Choose a destination box for the '
                             'calendar. (4) Hit "Generate calendar".'),
        },
    )
    #
    return render_template(
        'apps/calendarmaker/index.html',
        user=user,
        settingsText=settingsSummaryText,
        destBox=destBox,
        destBoxName=destBoxName,
        bgcolor=g.settings['color']['app_colors'][
            'calendar_maker_color']['value'],
        calendarImages=calendarImages,
        coverImageFileObject=coverImageFileObject,
        numRequiredImages=numRequiredImages,
        canGenerate=canGenerate,
        generationMessages=generationMessages,
        **pageFeatures,
    )


@app.route('/apps/calendarmaker/generate')
def calendarMakerGenerateCalendar():
    """
        Calendar actual generation view.
        Handles everything:
            building temporary image files
            driving the engine functions to make the pdf
            inserting the pdf in the box
            removing temporary files
    """
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'calendarMakerIndexView',
    )
    #
    destBoxString = request.cookies.get('apps_calendarmaker_destbox')
    currentCalendar = cookiesToCurrentCalendar(request.cookies)
    coverImagePathString = currentCalendar.get('cover_image_path_string')
    calendarImagePaths = currentCalendar.get('image_path_strings', [])
    cProps = currentCalendar.get('properties', {})
    #
    if destBoxString is None:
        destBox = None
    else:
        destBoxPath = splitPathString(destBoxString)
        destBox = getBoxFromPath(db, destBoxPath, user)
    if coverImagePathString is None:
        coverImageFileObject = None
    else:
        coverImageFileObject = pathToFileStructure(
            db,
            user,
            coverImagePathString,
        )
    #
    calendarImages = [
        pathToFileStructure(db, user, imgPath)
        for imgPath in calendarImagePaths
    ]
    numRequiredImages = countMonths(
        cProps.get('year0'),
        cProps.get('month0'),
        cProps.get('year1'),
        cProps.get('month1'),
    )
    if (destBox is None or coverImageFileObject is None or
            any([ci is None for ci in calendarImages])
            or numRequiredImages is None
            or numRequiredImages > len(calendarImages)):
        raise OstracionError('Cannot generate calendar')
    else:
        fileStorageDirectory = g.settings['system']['system_directories'][
            'fs_directory']['value']
        # proceed with generation
        tempFileDirectory = g.settings['system']['system_directories'][
            'temp_directory']['value']
        mkDirP(tempFileDirectory)
        texImageCoverPath = duplicateImageForCalendar(
            fileIdToPath(
                coverImageFileObject['file'].file_id,
                fileStorageDirectory=fileStorageDirectory,
            ),
            os.path.join(
                tempFileDirectory,
                '%s.%s' % (
                    uuid4().hex,
                    admittedImageMimeTypeToExtension[
                        coverImageFileObject['file'].mime_type
                    ],
                )
            ),
        )
        texImagePaths = [
            duplicateImageForCalendar(
                fileIdToPath(
                    imageFile['file'].file_id,
                    fileStorageDirectory=fileStorageDirectory,
                ),
                os.path.join(
                    tempFileDirectory,
                    '%s.%s' % (
                        uuid4().hex,
                        admittedImageMimeTypeToExtension[
                            imageFile['file'].mime_type
                        ],
                    )
                ),
            )
            for imageFile in calendarImages
        ]
        #
        fsDeletionQueue = [texImageCoverPath] + texImagePaths
        createdPdfTitle = uuid4().hex
        createdFile, creationToDelete = makeCalendarPdf(
            cProps,
            texImagePaths,
            texImageCoverPath,
            tempFileDirectory,
            createdPdfTitle,
        )
        #
        if createdFile is not None:
            # name and description
            calDescription = 'Calendar %i/%i - %i/%i' % (
                cProps['month0'],
                cProps['year0'],
                cProps['month1'],
                cProps['year1'],
            )
            calFileName = findFirstAvailableObjectNameInBox(
                db,
                destBox,
                'calendar_',
                '.pdf',
            )
            # place the pdf in the box
            placeFSFileInBox(
                db,
                user,
                fileStorageDirectory,
                destBox,
                createdFile,
                calFileName,
                calDescription,
            )
            # flushing the delete queue
            flushFsDeleteQueue(
                fsDeletionQueue + creationToDelete + [createdFile]
            )
            # messaging the user
            successMessage = ('Calendar generated. Please find the file '
                              '"%s" in the destination box.') % calFileName
            flashMessage('Success', 'Info', successMessage)
            # redirecting user to box
            return redirect(url_for('lsView', lsPathString=destBoxString))
        else:
            # flushing the delete queue
            flushFsDeleteQueue(
                fsDeletionQueue + creationToDelete + [createdFile],
            )
            # messaging the user
            flashMessage('Error', 'Error', 'Could not generate the calendar')
            return redirect(url_for('calendarMakerIndexView'))


@app.route('/apps/calendarmaker/resetsettings')
def calendarMakerResetSettingsView():
    """Reset calendar settings view."""
    request._onErrorUrl = url_for(
        'calendarMakerIndexView',
    )
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
    """Calendar settings form view."""
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
        startingweekday = safeInt(form.startingweekday.data, 6)
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
        form.month0.data = str(applyDefault(cProps.get('month0'), 1))
        form.year0.data = applyDefault(cProps.get('year0'), currentYear)
        form.month1.data = str(applyDefault(cProps.get('month1'), 12))
        form.year1.data = applyDefault(cProps.get('year1'), currentYear)
        form.language.data = applyDefault(cProps.get('language'), 'en')
        form.startingweekday.data = applyDefault(
            cProps.get('startingweekday'),
            6,
        )
        #
        pageFeatures = prepareTaskPageFeatures(
            appsPageDescriptor,
            ['root', 'calendar_maker', 'settings'],
            g,
        )
        #
        return render_template(
            'apps/calendarmaker/settings.html',
            user=user,
            bgcolor=g.settings['color']['app_colors'][
                'calendar_maker_color']['value'],
            form=form,
            **pageFeatures,
        )


@app.route('/apps/calendarmaker/browsebox/<mode>')
def calendarMakerBrowseBoxView(mode):
    """
        Three-way view to manage image-selection browsing box: handles
            reset
            initiate box selection (through preparePickBoxPageView)
            complete box selection
    """
    user = g.user
    db = dbGetDatabase()
    request._onErrorUrl = url_for(
        'calendarMakerImagesView',
    )
    if mode == 'start':
        rootBox = getRootBox(db)
        return preparePickBoxPageView(
            db=db,
            user=user,
            callbackUrl=url_for('calendarMakerBrowseBoxView', mode='end'),
            startBox=rootBox,
            message='Choose box to browse images from',
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
        Three-way view to manage pdf destination box: handles
            reset
            initiate box selection (through preparePickBoxPageView)
            complete box selection
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

        return preparePickBoxPageView(
            db=db,
            user=user,
            callbackUrl=url_for('calendarMakerDestBoxView', mode='end'),
            startBox=rootBox,
            predicate=writableRichBoxPicker,
            message='Choose the box where the calendar will be created',
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
    """Calendar cover image selection view (uses quoted coverObjPath)."""
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
    """Calendar cover image unset view."""
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
    """Calendar image-list unset view."""
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
    """Calendar image-selection page view."""
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
        coverImageFileObject = pathToFileStructure(
            db,
            user,
            coverImagePathString,
        )
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
            if file.mime_type in admittedImageMimeTypeToExtension
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
    pageFeatures = prepareTaskPageFeatures(
        appsPageDescriptor,
        ['root', 'calendar_maker', 'images'],
        g,
    )
    return render_template(
        'apps/calendarmaker/images.html',
        user=user,
        browseBox=browseBox,
        browseBoxName=browseBoxName,
        choosableFiles=choosableFiles,
        coverImageFileObject=coverImageFileObject,
        bgcolor=g.settings['color']['app_colors'][
            'calendar_maker_color']['value'],
        bgcolorbrowse=g.settings['color']['app_colors'][
            'calendar_maker_browse_color']['value'],
        calendarImages=calendarImages,
        numRequiredImages=numRequiredImages,
        **pageFeatures,
    )


@app.route('/apps/calendarmaker/addimage/<imageObjPath>')
def calendarMakerAddImage(imageObjPath):
    """Calendar image-list add-image view (through quoted imageObjPath)."""
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
    """Calendar image-list remove-one view."""
    request._onErrorUrl = url_for(
        'calendarMakerImagesView',
    )
    return applyReindexingToImages(request, {index: None})


@app.route('/apps/calendarmaker/swapimages/<int:index1>/<int:index2>')
def calendarMakerSwapImages(index1, index2):
    """Calendar image-list shift-one view."""
    request._onErrorUrl = url_for(
        'calendarMakerImagesView',
    )
    return applyReindexingToImages(
        request,
        {
            index1: index2,
            index2: index1,
        },
    )
