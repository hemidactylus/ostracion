""" uploads.py
    Views related to uploading,creating and editing files.
"""

import datetime

from werkzeug.utils import secure_filename

from flask import (
    render_template,
    redirect,
    url_for,
    g,
    request,
)

from ostracion_app.app_main import app

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.viewTools.messageTools import flashMessage

from ostracion_app.utilities.models.File import File

from ostracion_app.utilities.fileIO.postProcessing import (
    determineFileProperties,
)

from ostracion_app.utilities.database.fileSystem import (
    getBoxFromPath,
    getFileFromParent,
    updateFile,
)

from ostracion_app.utilities.database.settingsTools import (
    makeSettingImageUrl,
)

from ostracion_app.utilities.fileIO.thumbnails import (
    pickFileThumbnail,
)

from ostracion_app.utilities.fileIO.physical import (
    fileIdToPath,
)

from ostracion_app.utilities.fileIO.fileStorage import (
    saveAndAnalyseFilesInBox,
)

from ostracion_app.utilities.tools.formatting import (
    applyDefault,
)

from ostracion_app.utilities.viewTools.pathTools import (
    makeBreadCrumbs,
    splitPathString,
    prepareFileActions,
    prepareFileInfo,
    describeBoxTitle,
)

from ostracion_app.utilities.forms.forms import (
    UploadSingleFileForm,
    UploadMultipleFilesForm,
    MakeTextFileForm,
    EditTextFileForm,
)

from ostracion_app.utilities.tools.SavableTextFile import (
    SavableTextFile,
)


@app.route('/mktext', methods=['GET', 'POST'])
@app.route('/mktext/', methods=['GET', 'POST'])
@app.route('/mktext/<path:fsPathString>', methods=['GET', 'POST'])
def makeTextFileView(fsPathString=''):
    """Generate-new-text-file route."""
    user = g.user
    form = MakeTextFileForm()
    db = dbGetDatabase()
    boxPath = splitPathString(fsPathString)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    parentBoxPath = boxPath
    parentBox = getBoxFromPath(db, parentBoxPath, user)
    if form.validate_on_submit():
        fileName = secure_filename(form.filename.data)
        savableFile = SavableTextFile('')
        filesToUpload = [
            {
                'box_id': parentBox.box_id,
                'name': fileName,
                'description': form.filedescription.data,
                'date': datetime.datetime.now(),
                'fileObject': savableFile,
            }
        ]
        makeThumbnails = g.settings['behaviour']['behaviour_appearance'][
            'extract_thumbnails']['value']
        savingResult = saveAndAnalyseFilesInBox(
            db=db,
            files=filesToUpload,
            parentBox=parentBox,
            user=user,
            fileStorageDirectory=fileStorageDirectory,
            thumbnailFormat='thumbnail' if makeThumbnails else None,
            pastActionVerbForm='created',
        )
        flashMessage('Success', 'Info', savingResult)
        return redirect(url_for(
            'editTextFileView',
            fsPathString='/'.join(parentBoxPath[1:] + [fileName]),
        ))
    else:
        pathBCrumbs = makeBreadCrumbs(
            parentBoxPath,
            g,
            appendedItems=[{
                'kind': 'link',
                'target': None,
                'name': 'New text',
            }],
        )
        return render_template(
            'maketextfile.html',
            form=form,
            user=user,
            breadCrumbs=pathBCrumbs,
            iconUrl=pickFileThumbnail('text/plain'),
            pageTitle='New text',
            pageSubtitle='Create a new text file in "%s"' % (
                describeBoxTitle(parentBox)
            ),
        )


@app.route('/edittextfile/<path:fsPathString>', methods=['GET', 'POST'])
@app.route('/edittextfile', methods=['GET', 'POST'])
@app.route('/edittextfile/', methods=['GET', 'POST'])
def editTextFileView(fsPathString=''):
    """Edit-text-file route."""
    user = g.user
    db = dbGetDatabase()
    lsPath = splitPathString(fsPathString)
    boxPath, fileName = lsPath[:-1], lsPath[-1]
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    parentBox = getBoxFromPath(db, boxPath, user)
    file = getFileFromParent(db, parentBox, fileName, user)
    if file is None:
        raise OstracionError('File not found.')
    else:
        fileActions = prepareFileActions(
            db,
            file,
            boxPath[1:] + [file.name],
            parentBox,
            user,
            discardedActions={'text_edit'},
        )
        fileInfo = prepareFileInfo(db, file)
        #
        form = EditTextFileForm()
        ##
        form.textformat.choices = [
            ('plain', 'Plain'),
            ('markdown', 'Markdown'),
        ]
        ##
        if form.validate_on_submit():
            newcontents = form.filecontents.data
            filePath = fileIdToPath(
                file.file_id,
                fileStorageDirectory=fileStorageDirectory,
            )
            with open(filePath, 'w') as openFile:
                openFile.write('%s' % newcontents)
            # file properties
            fileProperties = determineFileProperties(filePath)
            newFile = File(**file.asDict())
            newFile.mime_type = fileProperties['file_mime_type']
            newFile.type = fileProperties['file_type']
            newFile.size = fileProperties['file_size']
            newFile.textual_mode = form.textformat.data
            newFile.editor_username = (user.username
                                       if user.is_authenticated
                                       else '')
            updateFile(db, boxPath, file.name, newFile, user)
            #
            flashMessage('Info', 'Info', 'File "%s" saved.' % file.name)
            return redirect(
                url_for(
                    'lsView',
                    lsPathString='/'.join(boxPath[1:]),
                )
            )
        else:
            form.filecontents.data = applyDefault(
                form.filecontents.data,
                open(
                    fileIdToPath(
                        file.file_id,
                        fileStorageDirectory=fileStorageDirectory,
                    )
                ).read(),
            )
            form.textformat.data = applyDefault(
                form.textformat.data,
                file.textual_mode,
                additionalNulls=['None'],
            )
            pathBCrumbs = makeBreadCrumbs(
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
                        'name': 'Edit text',
                    }
                ],
            )
            return render_template(
                'edittextfile.html',
                user=user,
                form=form,
                fileActions=fileActions,
                fileInfo=fileInfo,
                pageTitle='"%s" file edit' % file.name,
                pageSubtitle='Click "Save" to commit the changes',
                breadCrumbs=pathBCrumbs,
            )


@app.route('/upl', methods=['GET', 'POST'])
@app.route('/upl/', methods=['GET', 'POST'])
@app.route('/upl/<path:fsPathString>', methods=['GET', 'POST'])
def uploadSingleFileView(fsPathString=''):
    """Upload-a-file (to a box) route."""
    user = g.user
    form = UploadSingleFileForm()
    db = dbGetDatabase()
    boxPath = splitPathString(fsPathString)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    parentBoxPath = boxPath
    parentBox = getBoxFromPath(db, parentBoxPath, user)
    #
    if form.validate_on_submit():
        uploadedFile = form.file.data
        fileName = secure_filename(
            form.filename.data
            if len(form.filename.data) > 0
            else uploadedFile.filename
        )
        filesToUpload = [
            {
                'box_id': parentBox.box_id,
                'name': fileName,
                'description': form.filedescription.data,
                'date': datetime.datetime.now(),
                'fileObject': uploadedFile,
            }
        ]
        makeThumbnails = g.settings['behaviour']['behaviour_appearance'][
            'extract_thumbnails']['value']
        savingResult = saveAndAnalyseFilesInBox(
            db=db,
            files=filesToUpload,
            parentBox=parentBox,
            user=user,
            fileStorageDirectory=fileStorageDirectory,
            thumbnailFormat='thumbnail' if makeThumbnails else None,
        )
        flashMessage('Success', 'Info', savingResult)
        return redirect(url_for(
            'lsView',
            lsPathString='/'.join(parentBoxPath[1:]),
        ))
    else:
        pathBCrumbs = makeBreadCrumbs(
            parentBoxPath,
            g,
            appendedItems=[{
                'kind': 'link',
                'target': None,
                'name': 'Single upload',
            }],
        )
        return render_template(
            'uploadsinglefile.html',
            form=form,
            user=user,
            breadCrumbs=pathBCrumbs,
            pageTitle='Upload new file',
            pageSubtitle='Upload a new file to box "%s"' % (
                describeBoxTitle(parentBox)
            ),
            iconUrl=makeSettingImageUrl(g, 'app_images', 'single_upload'),
        )


@app.route('/uplm', methods=['GET', 'POST'])
@app.route('/uplm/', methods=['GET', 'POST'])
@app.route('/uplm/<path:fsPathString>', methods=['GET', 'POST'])
def uploadMultipleFilesView(fsPathString=''):
    """Upload-several-files (to a box) route."""
    user = g.user
    form = UploadMultipleFilesForm()
    db = dbGetDatabase()
    boxPath = splitPathString(fsPathString)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    parentBoxPath = boxPath
    parentBox = getBoxFromPath(db, parentBoxPath, user)
    #
    if form.validate_on_submit():
        uploadedFiles = [
            uf
            for uf in request.files.getlist('files')
            if uf.filename != ''
        ]
        #
        filesToUpload = [
            {
                'box_id': parentBox.box_id,
                'name': secure_filename(uploadedFile.filename),
                'description': form.filesdescription.data,
                'date': datetime.datetime.now(),
                'fileObject': uploadedFile,
            }
            for uploadedFile in uploadedFiles
        ]
        makeThumbnails = g.settings['behaviour']['behaviour_appearance'][
            'extract_thumbnails']['value']
        savingResult = saveAndAnalyseFilesInBox(
            db=db,
            files=filesToUpload,
            parentBox=parentBox,
            user=user,
            fileStorageDirectory=fileStorageDirectory,
            thumbnailFormat='thumbnail' if makeThumbnails else None,
        )
        flashMessage('Success', 'Info', savingResult)
        return redirect(url_for(
            'lsView',
            lsPathString='/'.join(parentBoxPath[1:]),
        ))
    else:
        pathBCrumbs = makeBreadCrumbs(
            parentBoxPath,
            g,
            appendedItems=[{
                'kind': 'link',
                'target': None,
                'name': 'Multiple upload',
            }],
        )
        return render_template(
            'uploadmultiplefiles.html',
            form=form,
            user=user,
            breadCrumbs=pathBCrumbs,
            pageTitle='Upload new files',
            pageSubtitle='Upload new files to box "%s"' % (
                describeBoxTitle(parentBox)
            ),
            iconUrl=makeSettingImageUrl(g, 'app_images', 'multiple_upload')
        )
