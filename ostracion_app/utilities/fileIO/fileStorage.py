""" fileStorage.py
    Module for handling storage of files,
    both as regular uploads and as thumbnails.
"""

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries,
)

from ostracion_app.utilities.fileIO.postProcessing import (
    determineFileProperties,
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.fileIO.physical import (
    fileIdToPath,
    temporaryFileName,
    flushFsDeleteQueue,
)

from ostracion_app.utilities.fileIO.thumbnails import (
    isImageMimeType,
    makeFileThumbnail,
    makeTempFileIntoThumbnail,
)

from ostracion_app.utilities.database.fileSystem import (
    getFileFromParent,
    deleteFile,
    makeFileInParent,
    updateFileThumbnail,
    updateLinkThumbnail,
    updateUserThumbnail,
    updateBoxThumbnail,
    isBoxNameUnderParentBox,
    isFileNameUnderParentBox,
)

from ostracion_app.utilities.database.settingsTools import (
    updateSettingThumbnail,
)

from ostracion_app.utilities.database.permissions import (
    userHasPermission,
    userIsAdmin,
)

from ostracion_app.utilities.fileIO.physical import (
    flushFsDeleteQueue,
)

from ostracion_app.utilities.models.File import File

# App-items handling import
from ostracion_app.views.apps.appRegisteredPlugins import (
    appsSetIconModes,
)


def saveAndAnalyseFilesInBox(db, files, parentBox, user, thumbnailFormat,
                             fileStorageDirectory,
                             pastActionVerbForm='uploaded'):
    """ Save files and enrich them with type/mimetype,
        unless something fails - this handles overwrites
        (file-on-file) and blockades (file has same name as box)
    """
    #
    # checking for name clashes with boxes
    if any(
        isBoxNameUnderParentBox(db, parentBox, fName)
        for fName in (
            fObj['name']
            for fObj in files
        )
    ):
        raise OstracionError('Files cannot have the name of existing boxes')
    else:
        if not userHasPermission(db, user, parentBox.permissions, 'w'):
            raise OstracionError('User has no write permission on this box')
        else:
            userName = user.username
            fsDeletionQueue = []
            numReplacements = 0
            #
            for file in files:
                newFile = File(**recursivelyMergeDictionaries(
                    {
                        k: v
                        for k, v in file.items()
                        if k != 'fileObject'
                    },
                    defaultMap={
                        'creator_username': userName,
                        'icon_file_id_username': userName,
                        'metadata_username': userName,
                        'editor_username': userName,
                        'textual_mode': 'plain',
                    },
                ))
                # are we overwriting a file?
                if isFileNameUnderParentBox(db, parentBox, newFile.name):
                    # delete the old file entry
                    # AND mark the file and its thumbnail
                    # (if any) for later deletion
                    prevFile = getFileFromParent(
                        db,
                        parentBox,
                        newFile.name,
                        user,
                    )
                    fsDeletionQueue += deleteFile(
                        db,
                        parentBox,
                        prevFile,
                        user,
                        fileStorageDirectory=fileStorageDirectory,
                        skipCommit=True,
                    )
                    numReplacements += 1
                #
                filePath = fileIdToPath(
                    newFile.file_id,
                    fileStorageDirectory=fileStorageDirectory,
                )
                file['fileObject'].save(filePath)
                #
                fileProperties = determineFileProperties(filePath)
                newFile.mime_type = fileProperties['file_mime_type']
                newFile.type = fileProperties['file_type']
                newFile.size = fileProperties['file_size']
                #
                if (thumbnailFormat is not None and
                        isImageMimeType(newFile.mime_type)):
                    # thumbnail preparation
                    fileThumbnailId, fileThumbnailMimeType = makeFileThumbnail(
                        newFile.file_id,
                        newFile.mime_type,
                        thumbnailFormat=thumbnailFormat,
                        fileStorageDirectory=fileStorageDirectory,
                    )
                    if fileThumbnailId is not None:
                        newFile.icon_file_id = fileThumbnailId
                        newFile.icon_mime_type = fileThumbnailMimeType
                #
                makeFileInParent(db, parentBox=parentBox, newFile=newFile)
            flushFsDeleteQueue(fsDeletionQueue)
            db.commit()
            return '%i file%s %s successfully%s.' % (
                len(files),
                '' if len(files) == 1 else 's',
                pastActionVerbForm,
                '' if numReplacements == 0 else (
                    ' (%i replaced)' % numReplacements
                )
            )


def storeFileAsThumbnail(db, fileToSave, mode, thumbnailFormat, targetItem,
                         parentBox, user, tempFileDirectory,
                         fileStorageDirectory):
    """ Handle setting/unsetting of thumbnail for various items
        (box,file,user,setting,user-as-admin).

        If a file to save is provided:
            store the file on the temp dir
            and if it is a valid thumbnail deal with its preparation
            and setting on the item, including possibly deletion of
            the previous thumbnail if necessary.
        if None is passed:
            simply delete any previous thumbnail if present

        Return True iff the (un/)setting is successful
    """
    # permission checks
    if mode == 'b':
        if not userHasPermission(db, user, targetItem.permissions, 'w'):
            raise OstracionError('User has no icon permission on this item')
    elif mode == 'f':
        if not userHasPermission(db, user, parentBox.permissions, 'w'):
            raise OstracionError('User has no icon permission on this item')
    elif mode == 'l':
        if not userHasPermission(db, user, parentBox.permissions, 'w'):
            raise OstracionError('User has no icon permission on this item')
    elif mode == 'u':
        if user.username != targetItem.username:
            raise OstracionError('Insufficient permissions')
    elif mode == 'au':
        if not userIsAdmin(db, user):
            raise OstracionError('Insufficient permissions')
    elif mode == 's':
        if not userIsAdmin(db, user):
            raise OstracionError('Insufficient permissions')
    #
    if fileToSave is not None:
        tempFileName = temporaryFileName(tempFileDirectory=tempFileDirectory)
        fileToSave.save(tempFileName)
        fileProperties = determineFileProperties(tempFileName)
    else:
        tempFileName = None
    #
    failures = False
    if tempFileName is None:
        thumbnailId = None
        thbMimeType = None
    else:
        if isImageMimeType(fileProperties['file_mime_type']):
            # make thumbnail and get the new ID
            thumbnailId, thbMimeType = makeTempFileIntoThumbnail(
                tempFileName,
                thumbnailFormat=thumbnailFormat,
                fileStorageDirectory=fileStorageDirectory,
            )
        else:
            failures = True
    if not failures:
        # un/set the icon ID
        if mode == 'f':
            fsDeleteQueue = updateFileThumbnail(
                db,
                targetItem,
                thumbnailId,
                thbMimeType,
                user,
                fileStorageDirectory=fileStorageDirectory
            )
        elif mode == 'l':
            fsDeleteQueue = updateLinkThumbnail(
                db,
                targetItem,
                thumbnailId,
                thbMimeType,
                user,
                fileStorageDirectory=fileStorageDirectory
            )
        elif mode == 'b':
            fsDeleteQueue = updateBoxThumbnail(
                db,
                targetItem,
                thumbnailId,
                thbMimeType,
                user,
                fileStorageDirectory=fileStorageDirectory
            )
        elif mode in {'u', 'au'}:
            fsDeleteQueue = updateUserThumbnail(
                db,
                targetItem,
                thumbnailId,
                thbMimeType,
                user,
                fileStorageDirectory=fileStorageDirectory
            )
        elif mode == 's':
            fsDeleteQueue = updateSettingThumbnail(
                db,
                targetItem,
                thumbnailId,
                thbMimeType,
                user,
                fileStorageDirectory=fileStorageDirectory
            )
        else:
            if mode in appsSetIconModes:
                fsDeleteQueue = appsSetIconModes[mode]['changers'][
                        'thumbnailUpdater'](
                    db,
                    targetItem,
                    thumbnailId,
                    thbMimeType,
                    user,
                    fileStorageDirectory=fileStorageDirectory
                )
            else:
                raise NotImplementedError(
                    'Unhandled storeFileAsThumbnail mode'
                )
        flushFsDeleteQueue(fsDeleteQueue)
    #
    return not failures
