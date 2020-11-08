"""
    utilities.py
"""

import shutil
import datetime
import urllib.parse

from flask import (
    redirect,
    url_for,
    render_template,
    request,
    g,
)

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries,
)

from ostracion_app.utilities.database.settingsTools import (
    makeSettingImageUrl,
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.tools.treeTools import (
    getMaxTreeDepth,
    collectTreeFromBox,
)

from ostracion_app.utilities.tools.colorTools import (
    prepareColorShadeMap,
)

from ostracion_app.utilities.database.fileSystem import (
    getBoxFromPath,
    getFileFromParent,
    splitPathString,
    isNameUnderParentBox,
    makeFileInParent,
)

from ostracion_app.utilities.fileIO.postProcessing import (
    determineFileProperties,
)

from ostracion_app.utilities.fileIO.physical import (
    fileIdToPath,
)

from ostracion_app.utilities.models.File import File

from ostracion_app.utilities.database.permissions import (
    userHasRole,
    userHasPermission,
)

from ostracion_app.utilities.fileIO.thumbnails import (
    isImageMimeType,
    makeFileThumbnail,
)

from ostracion_app.views.viewTools.pageTreeDescriptorTools import (
    filterPageDescriptor,
)

from ostracion_app.views.apps.appsPageTreeDescriptor import appsPageDescriptor


def selectAvailableApps(db, user):
    return filterPageDescriptor(
        appsPageDescriptor,
        subTasksAccessibility={
            'root': {
                'calendar_maker':  userHasRole(
                    db,
                    user,
                    'app',
                    'calendarmaker'
                ),
            },
        },
    )


def preparePickBoxPage(db, user, callbackUrl, startBox, message,
                       predicate=lambda richFileOrBox: True):
    #
    dstBoxTree = collectTreeFromBox(
        db,
        startBox,
        user,
        admitFiles=False,
        fileOrBoxEnricher=lambda richBox: {
            'obj_path': urllib.parse.quote_plus('/'.join(richBox['path'])),
        },
        predicate=predicate,
    )
    #
    maxDepth = getMaxTreeDepth(dstBoxTree)
    colorShadeMap = prepareColorShadeMap(
        g.settings['color']['navigation_colors']['box']['value'],
        g.settings['color']['tree_shade_colors'][
            'shade_treeview_pickbox']['value'],
        numShades=1 + maxDepth,
    )
    #
    return render_template(
        'dirtreeview.html',
        tree=dstBoxTree,
        mode='pick_box',
        object_quoted_path=callbackUrl,
        colorShadeMap=colorShadeMap,
        user=user,
        iconUrl=makeSettingImageUrl(g, 'app_images', 'move'),
        pageTitle='Choose a box',
        pageSubtitle=message,
        actions=None,
        backToUrl=None,
        breadCrumbs=[
            {
                'kind': 'link',
                'target': None,
                'name': 'Move box',
            },
        ],
    )


def placeFSFileInBox(db, user, fileStorageDirectory, box, filePhysicalPath,
                     fileName, fileDescription, fileTextualMode='',
                     fileThumbnailFormat=None):
    #
    # can user write to box?
    if userHasPermission(db, user, box.permissions, 'w'):
        # is the name available?
        if not isNameUnderParentBox(db, box, fileName):
            protoFile = {
                'box_id': box.box_id,
                'name': fileName,
                'description': fileDescription,
                'date': datetime.datetime.now(),
            }
            userName = user.username
            newFile = File(**recursivelyMergeDictionaries(
                protoFile,
                defaultMap={
                    'creator_username': userName,
                    'icon_file_id_username': userName,
                    'metadata_username': userName,
                    'editor_username': userName,
                    'textual_mode': fileTextualMode,
                },
            ))
            filePath = fileIdToPath(
                newFile.file_id,
                fileStorageDirectory=fileStorageDirectory,
            )
            shutil.copy2(filePhysicalPath, filePath)
            #
            fileProperties = determineFileProperties(filePath)
            newFile.mime_type = fileProperties['file_mime_type']
            newFile.type = fileProperties['file_type']
            newFile.size = fileProperties['file_size']
            #
            if (fileThumbnailFormat is not None and
                    isImageMimeType(newFile.mime_type)):
                # thumbnail preparation
                fileThumbnailId, fileThumbnailMimeType = makeFileThumbnail(
                    newFile.file_id,
                    newFile.mime_type,
                    thumbnailFormat=fileThumbnailFormat,
                    fileStorageDirectory=fileStorageDirectory,
                )
                if fileThumbnailId is not None:
                    newFile.icon_file_id = fileThumbnailId
                    newFile.icon_mime_type = fileThumbnailMimeType
            #
            makeFileInParent(db, parentBox=box, newFile=newFile)
            db.commit()
        else:
            raise OstracionError('Cannot create a file with that name')
    else:
        raise OstracionError('User has no write permission on box')
