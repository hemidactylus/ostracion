""" fileaccess.py
    Views related to navigating files in various ways.
"""

import urllib.parse

from flask import (
    redirect,
    url_for,
    render_template,
    g,
    send_from_directory,
    request,
    abort,
)

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries,
)

from ostracion_app.app_main import app

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.viewTools.messageTools import flashMessage

from ostracion_app.utilities.database.permissions import (
    userRoleRequired,
    userHasPermission,
)

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)

from ostracion_app.utilities.tools.formatting import (
    formatBytesSize,
    applyDefault,
    transformIfNotEmpty,
)

from ostracion_app.utilities.models.File import File

from ostracion_app.utilities.database.fileSystem import (
    getBoxFromPath,
    getFileFromParent,
    getFilesFromBox,
    splitPathString,
    deleteFile,
    updateFile,
    moveFile,
    getRootBox,
)

from ostracion_app.utilities.fileIO.physical import (
    fileIdToSplitPath,
    flushFsDeleteQueue,
)

from ostracion_app.utilities.tools.extraction import safeInt

from ostracion_app.utilities.viewTools.pathTools import (
    makeBreadCrumbs,
    prepareFileActions,
    prepareFileInfo,
    describeBoxTitle,
)

from ostracion_app.utilities.forms.forms import (
    FileDataForm,
    generateFsTicketForm,
)

from ostracion_app.utilities.tools.treeTools import (
    getMaxTreeDepth,
    collectTreeFromBox,
    treeAny,
)

from ostracion_app.utilities.tools.colorTools import (
    prepareColorShadeMap,
)

from ostracion_app.utilities.database.tickets import (
    dbMakeFileTicket,
)

from ostracion_app.utilities.database.settingsTools import (
    makeSettingImageUrl,
)

from ostracion_app.utilities.fileIO.fileTypes import (
    produceFileViewContents,
    isFileTextViewable,
)


@app.route('/fsg')
@app.route('/fsg/')
@app.route('/fsg/<path:fsPathString>')
def fsGalleryView(fsPathString=''):
    """ Gallery view route on a box.
        If just box, redirect to first file.
        If a file, use the ls of files to prepare prev/next links.

        That is to say, if user has read permission on box, gallery URLs are
        not index-based, rather filename-based and recalculated on actual 'ls'.
    """
    isTopAccess = 1 if safeInt(request.args.get('top'), 0) != 0 else 0
    user = g.user
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    db = dbGetDatabase()
    lsPath = splitPathString(fsPathString)
    # is it a box or a file?
    targetBox = getBoxFromPath(db, lsPath, user)
    if targetBox is not None:
        # if there are files, we redirect to the first one
        # otherwise, a message and falling back to ls view of the box
        files = sorted(
            getFilesFromBox(db, targetBox),
            key=lambda f: (f.name.lower(), f.name),
        )
        if len(files) > 0:
            return redirect(url_for(
                'fsGalleryView',
                fsPathString='/'.join(lsPath[1:] + [files[0].name]),
                top=str(isTopAccess),
            ))
        else:
            flashMessage(
                'Info',
                'Empty box',
                'Cannot view as gallery a box without files',
            )
            return redirect(url_for(
                'lsView',
                lsPathString='/'.join(lsPath[1:]),
            ))
    else:
        # is it a file?
        boxPath, fileName = lsPath[:-1], lsPath[-1]
        parentBox = getBoxFromPath(db, boxPath, user)
        file = getFileFromParent(db, parentBox, fileName, user)
        if file is not None:
            if isTopAccess:
                # gallery navigation calculations
                files = sorted(
                    getFilesFromBox(db, parentBox),
                    key=lambda f: (f.name.lower(), f.name),
                )
                thisFileIndex = [
                    idx
                    for idx, fil in enumerate(files)
                    if fil.name == fileName
                ][0]
                numGalleryFiles = len(files)
                nextFileIndex = (thisFileIndex + 1) % numGalleryFiles
                prevFileIndex = (
                    thisFileIndex - 1 + numGalleryFiles
                ) % numGalleryFiles
                #
                pathBCrumbs = makeBreadCrumbs(
                    boxPath,
                    g,
                    appendedItems=[{
                        'kind': 'link',
                        'name': 'Gallery view %i/%i' % (
                            thisFileIndex + 1,
                            numGalleryFiles,
                        ),
                        'target': None,
                    }],
                )
                fileContents = produceFileViewContents(
                    db,
                    file,
                    mode='fsview',
                    viewParameters={
                        'boxPath': boxPath,
                        'fileName': fileName,
                    },
                    fileStorageDirectory=fileStorageDirectory,
                )
                fileActions = {
                    'gallery_prev': url_for(
                        'fsGalleryView',
                        fsPathString='/'.join(
                            boxPath[1:] + [files[prevFileIndex].name]
                        ),
                        top=str(isTopAccess),
                    ),
                    'gallery_next': url_for(
                        'fsGalleryView',
                        fsPathString='/'.join(
                            boxPath[1:] + [files[nextFileIndex].name]
                        ),
                        top=str(isTopAccess),
                    ),
                    'gallery_up': url_for(
                        'lsView',
                        lsPathString='/'.join(boxPath[1:]),
                    ),
                    'download': url_for(
                        'fsDownloadView',
                        fsPathString=fsPathString,
                    ),
                }
                return render_template(
                    'fileview.html',
                    fileActions=fileActions,
                    fileInfo=None,
                    filecontents=fileContents,
                    breadCrumbs=pathBCrumbs,
                    user=user,
                    pageTitle='"%s" gallery, file "%s" (%i/%i)' % (
                        parentBox.title,
                        file.name,
                        thisFileIndex + 1,
                        numGalleryFiles,
                    ),
                    pageSubtitle=file.description,
                    downloadUrl=None,
                    hideBreadCrumbs=True,
                    hideNavbar=True,
                )
            else:
                return fsDownloadView(fsPathString=fsPathString)
        else:
            # extreme fallback to ls, which will hiearchically
            # deal with the retrieval
            return redirect(url_for('lsView', lsPathString=fsPathString))


@app.route('/fshv/<path:fsPathString>')
@app.route('/fshv/')
@app.route('/fshv')
def fsHybridView(fsPathString=''):
    """ "Hybrid" file view: if it is a textually-viewable file
        (such as plaintext but most importantly markdown), show it as 'view';
        if it is anything else (especially an image), return it as 'download':
        this is to make sure embedding of images in markdown documents works
        as usual.
    """
    user = g.user
    lsPath = splitPathString(fsPathString)
    boxPath, fileName = lsPath[:-1], lsPath[-1]
    db = dbGetDatabase()
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    parentBox = getBoxFromPath(db, boxPath, user)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    file = getFileFromParent(db, parentBox, fileName, user)
    isTextual = isFileTextViewable(file)
    if isTextual:
        return fsView(fsPathString=fsPathString)
    else:
        return fsDownloadView(fsPathString=fsPathString)


@app.route('/fsv/<path:fsPathString>')
@app.route('/fsv/')
@app.route('/fsv')
def fsView(fsPathString=''):
    """View file route. If not viewable, display an error message."""
    user = g.user
    lsPath = splitPathString(fsPathString)
    boxPath, fileName = lsPath[:-1], lsPath[-1]
    db = dbGetDatabase()
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    parentBox = getBoxFromPath(db, boxPath, user)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    file = getFileFromParent(db, parentBox, fileName, user)
    if file is not None:
        fileInfo = prepareFileInfo(db, file)
        fileActions = prepareFileActions(
            db,
            file,
            boxPath[1:] + [file.name],
            parentBox,
            user,
            discardedActions={'view'},
        )
        fileContents = produceFileViewContents(
            db,
            file,
            mode='fsview',
            viewParameters={
                'boxPath': boxPath,
                'fileName': fileName,
            },
            fileStorageDirectory=fileStorageDirectory,
        )
        #
        pathBCrumbs = makeBreadCrumbs(
            boxPath,
            g,
            appendedItems=[{
                'kind': 'file',
                'target': file,
            }],
        )
        #
        return render_template(
            'fileview.html',
            fileActions=fileActions,
            fileInfo=fileInfo,
            filecontents=fileContents,
            breadCrumbs=pathBCrumbs,
            user=user,
            pageTitle='"%s" file view' % file.name,
            pageSubtitle='%s (%s; %s)' % (
                file.description,
                file.type,
                formatBytesSize(file.size),
            ),
            downloadUrl=None,
        )
    else:
        return abort(404)


@app.route('/fsd/<path:fsPathString>')
@app.route('/fsd/')
@app.route('/fsd')
def fsDownloadView(fsPathString=''):
    """Download-file view."""
    user = g.user
    lsPath = splitPathString(fsPathString)
    boxPath, fileName = lsPath[:-1], lsPath[-1]
    db = dbGetDatabase()
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    parentBox = getBoxFromPath(db, boxPath, user)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    if parentBox is not None:
        file = getFileFromParent(db, parentBox, fileName, user)
        if file is not None:
            filePhysicalPath, filePhysicalName = fileIdToSplitPath(
                file.file_id,
                fileStorageDirectory=fileStorageDirectory,
            )
            return send_from_directory(
                filePhysicalPath,
                filePhysicalName,
                attachment_filename=file.name,
                as_attachment=True,
                mimetype=file.mime_type,
            )
        else:
            return abort(404, 'Content unavailable')
    else:
        return abort(404, 'Content unavailable')


@app.route('/fsrm/<path:fsPathString>')
@app.route('/fsrm/')
@app.route('/fsrm')
def fsDeleteFileView(fsPathString=''):
    """ Delete-file view.
        Permission checks are performed by the deleteFile filesystem call.
    """
    user = g.user
    db = dbGetDatabase()
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    lsPath = splitPathString(fsPathString)
    boxPath, fileName = lsPath[:-1], lsPath[-1]
    parentBox = getBoxFromPath(db, boxPath, user)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    file = getFileFromParent(db, parentBox, fileName, user)
    fsDeleteQueue = deleteFile(
        db,
        parentBox,
        file,
        user,
        fileStorageDirectory=fileStorageDirectory,
    )
    flushFsDeleteQueue(fsDeleteQueue)
    return redirect(url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    ))


@app.route('/mdfile/<path:fsPathString>', methods=['GET', 'POST'])
@app.route('/mdfile', methods=['GET', 'POST'])
@app.route('/mdfile/', methods=['GET', 'POST'])
def fsMetadataView(fsPathString=''):
    """Edit-file-metadata view, a web-form."""
    user = g.user
    db = dbGetDatabase()
    form = FileDataForm()
    lsPath = splitPathString(fsPathString)
    boxPath, prevFileName = lsPath[:-1], lsPath[-1]
    parentBox = getBoxFromPath(db, boxPath, user)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    file = getFileFromParent(db, parentBox, prevFileName, user)
    if form.validate_on_submit():
        newFile = File(
            **recursivelyMergeDictionaries(
                {
                    'name': form.filename.data,
                    'description': form.filedescription.data,
                    'metadata_username': user.username,
                },
                defaultMap=file.asDict(),
            )
        )
        updateFile(db, boxPath, prevFileName, newFile, user)
        return redirect(url_for('lsView', lsPathString='/'.join(boxPath[1:])))
    else:
        form.filename.data = applyDefault(
            form.filename.data,
            file.name
        )
        form.filedescription.data = applyDefault(
            form.filedescription.data,
            file.description
        )
        #
        pageFeatures = {
            'breadCrumbs': makeBreadCrumbs(
                boxPath,
                g,
                appendedItems=[
                    {
                        'kind': 'file',
                        'target': file,
                    },
                    {
                        'kind': 'link',
                        'target': None,
                        'name': 'Metadata',
                    }
                ],
            ),
            'pageTitle': 'Edit file metadata (%s)' % file.name,
            'pageSubtitle': 'Name is mandatory',
            'iconUrl': url_for(
                'fileThumbnailView',
                dummyId=file.icon_file_id + '_',
                fsPathString='/'.join(lsPath[1:]),
            ),
        }
        return render_template(
            'filedataedit.html',
            form=form,
            user=user,
            **pageFeatures,
        )


@app.route('/maketicketfile/<path:fsPathString>', methods=['GET', 'POST'])
@app.route('/maketicketfile', methods=['GET', 'POST'])
@app.route('/maketicketfile/', methods=['GET', 'POST'])
@userRoleRequired({('system', 'admin'), ('system', 'ticketer')})
def fsMakeTicketView(fsPathString=''):
    """Create-file-ticket (file-read) view."""
    user = g.user
    lsPath = splitPathString(fsPathString)
    boxPath, fileName = lsPath[:-1], lsPath[-1]
    db = dbGetDatabase()
    parentBox = getBoxFromPath(db, boxPath, user)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    if parentBox is not None:
        file = getFileFromParent(db, parentBox, fileName, user)
        if file is not None:
            pathBCrumbs = makeBreadCrumbs(
                boxPath,
                g,
                appendedItems=[
                    {
                        'kind': 'file',
                        'target': file,
                    },
                    {
                        'name': '(create ticket)',
                        'kind': 'link',
                        'target': url_for(
                            'fsMakeTicketView',
                            fsPathString=fsPathString,
                        ),
                        'link': False,
                    },
                ],
            )
            # if this succeeded, user has read permission on 'file'
            form = generateFsTicketForm(
                fileModePresent=True,
                settings=g.settings,
            )
            if form.validate_on_submit():
                magicLink = dbMakeFileTicket(
                    db=db,
                    ticketName=form.name.data,
                    validityHours=transformIfNotEmpty(
                        form.validityhours.data,
                        int,
                    ),
                    multiplicity=transformIfNotEmpty(
                        form.multiplicity.data,
                        int,
                    ),
                    ticketMessage=transformIfNotEmpty(
                        form.ticketmessage.data,
                    ),
                    file=file,
                    fileMode=form.filemode.data,
                    lsPath=lsPath,
                    user=user,
                    urlRoot=request.url_root,
                    settings=g.settings,
                )
                flashMessage(
                    'Success',
                    'Done',
                    ('File ticket generated. Give the recipient '
                     'the following magic link:'),
                    pillText=magicLink,
                )
                return redirect(url_for(
                    'lsView',
                    lsPathString='/'.join(boxPath[1:]),
                ))
            else:
                form.name.data = applyDefault(form.name.data, file.name)
                form.ticketmessage.data = applyDefault(
                    form.ticketmessage.data,
                    'Please access this file',
                )
                form.filemode.data = applyDefault(
                    form.filemode.data,
                    'direct',
                    additionalNulls=['None'],
                )
                maxValidityHours = g.settings['behaviour'][
                    'behaviour_tickets']['max_ticket_validityhours']['value']
                form.validityhours.data = applyDefault(
                    form.validityhours.data,
                    (str(maxValidityHours)
                     if maxValidityHours is not None
                     else ''),
                )
                maxMultiplicity = g.settings['behaviour'][
                    'behaviour_tickets']['max_ticket_multiplicity']['value']
                form.multiplicity.data = applyDefault(
                    form.multiplicity.data,
                    (str(maxMultiplicity)
                     if maxMultiplicity is not None
                     else ''),
                )
                return render_template(
                    'fsticket.html',
                    pageTitle='Create public file ticket',
                    pageSubtitle=('Recipient(s) of the ticket will be able '
                                  'to access "%s" without an account.') % (
                                      fsPathString,
                                  ),
                    baseMultiplicityCaption=('Number of granted accesses (bo'
                                             'th views and downloads count)'),
                    user=user,
                    form=form,
                    iconUrl=makeSettingImageUrl(
                        g,
                        'app_images',
                        'file_ticket',
                    ),
                    showFileMode=True,
                    breadCrumbs=pathBCrumbs,
                )
        else:
            return abort(404)
    else:
        return abort(404)


@app.route('/mvfile/<quotedFilePath>')
def fsMoveFileView(quotedFilePath):
    """Move-file, view 1/2: select destination box."""
    user = g.user
    db = dbGetDatabase()
    # first we find the file
    fsPathString = urllib.parse.unquote_plus(quotedFilePath)
    lsPath = splitPathString(fsPathString)
    boxPath, fileName = lsPath[:-1], lsPath[-1]
    parentBox = getBoxFromPath(db, boxPath, user)
    file = getFileFromParent(db, parentBox, fileName, user)
    # next we prepare the selectable destinations
    rootBox = getRootBox(db)

    def rbPredicate(richBox, idToAvoid=parentBox.box_id):
        return all((
            richBox['box'].box_id != idToAvoid,
            userHasPermission(db, user, richBox['box'].permissions, 'w')
        ))
    dstBoxTree = collectTreeFromBox(
        db,
        rootBox,
        user,
        admitFiles=False,
        fileOrBoxEnricher=lambda richBox: {
            'obj_path': urllib.parse.quote_plus('/'.join(richBox['path'])),
        },
        predicate=rbPredicate,
    )
    #
    maxDepth = getMaxTreeDepth(dstBoxTree)
    colorShadeMap = prepareColorShadeMap(
        g.settings['color']['navigation_colors']['file']['value'],
        g.settings['color']['tree_shade_colors'][
            'shade_treeview_pickbox']['value'],
        numShades=1 + maxDepth,
    )
    destinationsExist = treeAny(
        dstBoxTree,
        property=lambda node: node['predicate'],
    )
    #
    return render_template(
        'dirtreeview.html',
        tree=dstBoxTree if destinationsExist else None,
        mode='file_move',
        object_quoted_path=quotedFilePath,
        colorShadeMap=colorShadeMap,
        user=user,
        iconUrl=makeSettingImageUrl(g, 'app_images', 'move'),
        pageTitle='Select file destination',
        pageSubtitle=(('Choose the box to which file "%s" shall '
                       'be moved from "%s"') % (
                        file.name,
                        describeBoxTitle(parentBox),
                     )
        ),
        actions=None,
        backToUrl=None if destinationsExist else url_for(
            'lsView',
            lsPathString='/'.join(boxPath[1:]),
        ),
        breadCrumbs=makeBreadCrumbs(
            boxPath,
            g,
            appendedItems=[
                {
                    'kind': 'file',
                    'target': file,
                },
                {
                    'kind': 'link',
                    'target': None,
                    'name': 'Move file',
                }
            ],
        ),
    )


@app.route('/domvfile/<quotedFilePath>/<quotedDestBox>')
@app.route('/domvfile/<quotedFilePath>/')
@app.route('/domvfile/<quotedFilePath>')
def fsDoMoveFileView(quotedFilePath, quotedDestBox=''):
    """Move-file, view 2/2: dest box is selected, actually move."""
    user = g.user
    db = dbGetDatabase()
    # we retrieve the source file and the destination box
    srcFsPathString = urllib.parse.unquote_plus(quotedFilePath)
    srcLsPath = splitPathString(srcFsPathString)
    srcBoxPath, fileName = srcLsPath[:-1], srcLsPath[-1]
    srcBox = getBoxFromPath(db, srcBoxPath, user)
    file = getFileFromParent(db, srcBox, fileName, user)
    dstBoxPathString = urllib.parse.unquote_plus(quotedDestBox)
    dstBoxPath = splitPathString(dstBoxPathString)
    dstBox = getBoxFromPath(db, dstBoxPath, user)
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    #
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(srcBoxPath[1:]),
    )
    messages = moveFile(
        db,
        file,
        srcBox,
        dstBox,
        user,
        fileStorageDirectory=fileStorageDirectory,
    )
    for msg in messages:
        flashMessage('Info', 'Info', msg)
    return redirect(url_for(
        'lsView',
        lsPathString='/'.join(dstBoxPath[1:]),
    ))
