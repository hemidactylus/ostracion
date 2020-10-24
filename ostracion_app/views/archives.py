""" archives.py
    Views related to handling archives for up-
    and down-loading of whole trees
"""

import os

from flask import (
    current_app,
    abort,
    redirect,
    url_for,
    request,
    g,
)

from ostracion_app.app_main import app

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)

from ostracion_app.utilities.database.fileSystem import (
    getBoxesFromParent,
    splitPathString,
    getBoxFromPath,
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.tools.treeTools import (
    collectTreeFromBox,
    treeSize,
)

from ostracion_app.utilities.viewTools.pathTools import (
    describeBoxName,
    userCanDownloadArchive,
)

from ostracion_app.utilities.viewTools.messageTools import flashMessage

from ostracion_app.utilities.fileIO.physical import (
    flushFsDeleteQueue,
    fileIdToPath,
    temporaryFileName,
    temporarySplitFileName,
)

from ostracion_app.utilities.tools.formatting import (
    bytesToMiB,
    formatBytesSize,
)

from ostracion_app.utilities.tools.comparisonTools import (
    optionNumberLeq,
)

from ostracion_app.utilities.fileIO.zipFileUtilities import (
    makeZipFile,
)


@app.route('/dbox')
@app.route('/dbox/')
@app.route('/dbox/<path:boxPathString>')
def downloadBoxView(boxPathString=''):
    user = g.user
    lsPath = splitPathString(boxPathString)
    db = dbGetDatabase()
    #
    canDownloadArchive = userCanDownloadArchive(
        db,
        user,
        g.settings,
    )
    #
    if not canDownloadArchive:
        return abort(404)
    else:
        thisBox = getBoxFromPath(db, lsPath, user)
        if thisBox is not None:
            boxPath = lsPath[1:]
            tempFileDirectory = g.settings['system']['system_directories'][
                'temp_directory']['value']
            fileStorageDirectory = g.settings['system']['system_directories'][
                'fs_directory']['value']
            # we extract the tree "from this box downward"
            tree = collectTreeFromBox(db, thisBox, user, admitFiles=True)
            overallSize = treeSize(tree)
            # size-dependent handling by reading settings
            mibSize = bytesToMiB(overallSize)
            archiveWarningSizeMib = g.settings['behaviour']['archives'][
                'archive_download_alert_size']['value']
            archiveBlockSizeMib = g.settings['behaviour']['archives'][
                'archive_download_blocking_size']['value']
            if not optionNumberLeq(archiveBlockSizeMib, mibSize):
                # archive is simply too big (hard limit)
                oeText = ('Cannot prepare archive: box size, %s'
                          ', exceeds configured limits')

                raise OstracionError(oeText % formatBytesSize(overallSize))
            else:
                # we may have to issue a warning to the downloader:
                # this if (1) rather large archive,
                # (2) no previous 'ok' was given
                hasConfirmed = request.args.get('confirmed') == 'yes'
                if all([
                    not optionNumberLeq(archiveWarningSizeMib, mibSize),
                    not hasConfirmed,
                ]):
                    # we issue the warning and wait
                    confirmText = ('Preparing this archive may take some '
                                   'time due to the size of the box (%s). '
                                   'Click this message to really proceed '
                                   'with the download.')
                    flashMessage(
                        'Warning',
                        'Caution',
                        confirmText % formatBytesSize(overallSize),
                        url=url_for(
                            'downloadBoxView',
                            boxPathString=boxPathString,
                            confirmed='yes',
                        ),
                    )
                    return redirect(url_for(
                        'lsView',
                        lsPathString=boxPathString,
                    ))
                else:
                    # we collect the information needed to prepare the
                    # archive file. For now, no empty boxes
                    # (a zip format limitation)
                    def collectArchivablePairs(tr, accPath=''):
                        hereFiles = [
                            {
                                'type': 'file',
                                'path': fileIdToPath(
                                    file['file'].file_id,
                                    fileStorageDirectory,
                                ),
                                'zip_path': os.path.join(
                                    accPath,
                                    file['file'].name,
                                ),
                            }
                            for file in tr['contents']['files']
                        ] + [
                            {
                                'type': 'data',
                                'data': link['link'].formatAsString(),
                                'zip_path': os.path.join(
                                    accPath,
                                    '%s' % link['link'].name,
                                ),
                            }
                            for link in tr['contents']['links']
                        ]
                        subFiles = [
                            fp
                            for subBox in tr['contents']['boxes']
                            for fp in collectArchivablePairs(
                                subBox,
                                accPath=os.path.join(
                                    accPath,
                                    subBox['box'].box_name,
                                )
                            )
                        ]
                        return hereFiles + subFiles

                    # we make the tree into a list of filePairs, ready to zip
                    inPairs = collectArchivablePairs(tree)
                    filePairs = [p for p in inPairs if p['type'] == 'file']
                    dataPairs = [p for p in inPairs if p['type'] == 'data']
                    # we create the zip
                    _, archiveFileTitle = temporarySplitFileName(
                        tempFileDirectory,
                    )
                    makeZipFile(
                        os.path.join(tempFileDirectory, archiveFileTitle),
                        filePairs,
                        dataPairs,
                    )
                    # Now the file exists, ready to be served.
                    # Instead of a plain send_from_directory, though,
                    # we use the answer "Stream file, then delete"
                    # by Sean Vieira here:
                    # https://stackoverflow.com/questions/24612366/
                    #   delete-an-uploaded-file-after-downloading-it-from-flask

                    def StreamFileAndRemoveIt(localFileName):
                        fileHandle = open(localFileName, 'rb')
                        yield from fileHandle
                        fileHandle.close()
                        os.remove(localFileName)

                    zipFileName = '%s.zip' % describeBoxName(
                        thisBox,
                    )
                    contentDisposition = 'attachment; filename="%s"' % (
                        zipFileName,
                    )
                    return current_app.response_class(
                        StreamFileAndRemoveIt(
                            localFileName=os.path.join(
                                tempFileDirectory,
                                archiveFileTitle,
                            ),
                        ),
                        headers={
                            'Content-Disposition': contentDisposition,
                        },
                        mimetype='application/zip',
                    )
        else:
            request._onErrorUrl = url_for(
                'lsView',
                lsPathString='/'.join(lsPath[1:-1]),
            )
            raise OstracionWarning(
                'Cannot access the specified box "%s"' % lsPath[-1]
            )
