""" thumbnails.py
    Views to set, unset, retrieve thumbnails for various items
    based on provided (full-size) images.
"""

import os

from flask import (
    render_template,
    redirect,
    url_for,
    abort,
    g,
    send_from_directory,
    request,
)

from config import (
    defaultAppImageDirectory,
)

from ostracion_app.app_main import app

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries,
)

from ostracion_app.utilities.viewTools.messageTools import flashMessage

from ostracion_app.views.viewTools.thumbnailFormatFinder import (
    determineThumbnailFormatByModeAndTarget,
)

from ostracion_app.utilities.forms.forms import (
    UploadIconForm,
)

from ostracion_app.utilities.fileIO.physical import (
    fileIdToSplitPath,
)

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)
from ostracion_app.utilities.database.userTools import (
    dbGetUser,
)

from ostracion_app.utilities.database.fileSystem import (
    getBoxFromPath,
    getFileFromParent,
    getLinkFromParent,
)

from ostracion_app.utilities.database.settingsTools import (
    makeSettingImageUrl,
)

from ostracion_app.utilities.database.permissions import (
    userIsAdmin,
)

from ostracion_app.utilities.fileIO.thumbnails import (
    pickFileThumbnail,
)

from ostracion_app.utilities.fileIO.fileStorage import (
    saveAndAnalyseFilesInBox,
    storeFileAsThumbnail,
)

from ostracion_app.utilities.viewTools.pathTools import (
    makeBreadCrumbs,
    splitPathString,
    #
    prepareTaskPageFeatures,
)

from ostracion_app.views.viewTools.userProfilePageTreeDescriptor import (
    userProfilePageDescriptor,
)

from ostracion_app.views.viewTools.adminPageTreeDescriptor import (
    adminPageDescriptor,
)


@app.route('/favicon.ico')
def faviconView():
    """ Default favicon route -> application logo.
        In order to exploit the full settingThumbnailView
        behaviour, including sending the right mime-type,
        we directly call the route'd function here.
    """
    return settingThumbnailView(
        g.settings['image']['ostracion_images'][
            'navbar_logo']['setting'].value,
        'ostracion_images',
        'navbar_logo'
    )


@app.route('/filethumbnail/<dummyId>/<path:fsPathString>')
def fileThumbnailView(dummyId, fsPathString):
    """Route for access to thumbnail image files based on file path."""
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
    if (file is not None and
            file.icon_file_id is not None and
            file.icon_file_id != ''):
        filePhysicalPath, filePhysicalName = fileIdToSplitPath(
            file.icon_file_id,
            fileStorageDirectory=fileStorageDirectory,
        )
        return send_from_directory(
            filePhysicalPath,
            filePhysicalName,
            mimetype=file.icon_mime_type,
        )
    else:
        return redirect(
            pickFileThumbnail(file.mime_type)
        )


@app.route('/linkthumbnail/<dummyId>/<path:fsPathString>')
def linkThumbnailView(dummyId, fsPathString=''):
    """Route for access to thumbnail image files based on link path."""
    user = g.user
    lsPath = splitPathString(fsPathString)
    boxPath, linkName = lsPath[:-1], lsPath[-1]
    db = dbGetDatabase()
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    parentBox = getBoxFromPath(db, boxPath, user)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    link = getLinkFromParent(db, parentBox, linkName, user)
    if (link is not None and
            link.icon_file_id is not None and
            link.icon_file_id != ''):
        filePhysicalPath, filePhysicalName = fileIdToSplitPath(
            link.icon_file_id,
            fileStorageDirectory=fileStorageDirectory,
        )
        return send_from_directory(
            filePhysicalPath,
            filePhysicalName,
            mimetype=link.icon_mime_type,
        )
    else:
        return redirect(
            makeSettingImageUrl(g, 'app_images', 'external_link')
        )


@app.route('/boxthumbnail/<dummyId>/<path:boxPathString>')
@app.route('/boxthumbnail/<dummyId>/')
@app.route('/boxthumbnail/<dummyId>')
def boxThumbnailView(dummyId, boxPathString=''):
    """Route for access to thumbnail image files based on box path."""
    user = g.user
    db = dbGetDatabase()
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    if boxPathString == '':
        # root case
        return redirect(makeSettingImageUrl(g, 'app_images', 'root_box'))
    else:
        db = dbGetDatabase()
        boxPath = splitPathString(boxPathString)
        request._onErrorUrl = url_for(
            'lsView',
            lsPathString='/'.join(boxPath[1:]),
        )
        box = getBoxFromPath(db, boxPath, user)
        if (box is not None and
                box.icon_file_id is not None and
                box.icon_file_id != ''):
            filePhysicalPath, filePhysicalName = fileIdToSplitPath(
                box.icon_file_id,
                fileStorageDirectory=fileStorageDirectory,
            )
            return send_from_directory(
                filePhysicalPath,
                filePhysicalName,
                mimetype=box.icon_mime_type,
            )
        else:
            return redirect(makeSettingImageUrl(
                g,
                'app_images',
                'standard_box',
            ))


@app.route('/userthumbnail/<dummyId>/<username>')
@app.route('/userthumbnail/<dummyId>/<username>/')
def userThumbnailView(dummyId, username):
    """Route for access to thumbnail image files based on user name."""
    user = g.user
    db = dbGetDatabase()
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    if user.username == username or userIsAdmin(db, user):
        targetUser = (user
                      if user.username == username
                      else dbGetUser(db, username))
        if targetUser.icon_file_id != '':
            filePhysicalPath, filePhysicalName = fileIdToSplitPath(
                targetUser.icon_file_id,
                fileStorageDirectory=fileStorageDirectory,
            )
            return send_from_directory(
                filePhysicalPath,
                filePhysicalName,
                mimetype=targetUser.icon_mime_type,
            )
        else:
            return redirect(makeSettingImageUrl(g, 'user_images', 'user_icon'))
    else:
        return abort(400, 'User has no permission to access this resource.')


@app.route('/settingthumbnail/<dummyId>/<settingGroupId>/<settingId>')
@app.route('/settingthumbnail/<dummyId>/<settingGroupId>/<settingId>/')
def settingThumbnailView(dummyId, settingGroupId, settingId):
    """ Route for access to setting (of type image) thumbnail
        with live resolution of id-vs-default.
    """
    user = g.user
    db = dbGetDatabase()
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    setting = g.settings['image'][settingGroupId][settingId]['setting']
    if setting.klass != 'image':
        raise RuntimeError('unexpected setting of non-image klass')
    else:
        if setting.value != '':
            filePhysicalPath, filePhysicalName = fileIdToSplitPath(
                setting.value,
                fileStorageDirectory=fileStorageDirectory,
            )
            mimeType = setting.icon_mime_type
        else:
            filePhysicalPath = defaultAppImageDirectory
            filePhysicalName = setting.default_value
            mimeType = setting.default_icon_mime_type
        #
        return send_from_directory(
            filePhysicalPath,
            filePhysicalName,
            mimetype=mimeType,
        )


@app.route('/unseticon/<mode>/<path:itemPathString>')
@app.route('/unseticon/<mode>/')
@app.route('/unseticon/<mode>')
def unsetIconView(mode, itemPathString=''):
    """Route for explicit removal of thumbnail, if any, to various items."""
    if (mode == 'au' and
            not g.settings['behaviour']['behaviour_admin_powers'][
                'admin_is_god']['value']):
        request._onErrorUrl = url_for('adminHomeUsersView')
        raise OstracionError(
            'This feature is turned off in the configuration'
        )
    else:
        user = g.user
        form = UploadIconForm()
        db = dbGetDatabase()
        #
        tempFileDirectory = g.settings['system']['system_directories'][
            'temp_directory']['value']
        fileStorageDirectory = g.settings['system']['system_directories'][
            'fs_directory']['value']
        #
        if mode == 'b':
            modeName = 'box'
            boxPath = splitPathString(itemPathString)
            thisItem = getBoxFromPath(db, boxPath, user)
            parentBox = None
        elif mode == 'f':
            modeName = 'file'
            fullPath = splitPathString(itemPathString)
            boxPath, fileName = fullPath[:-1], fullPath[-1]
            parentBox = getBoxFromPath(db, boxPath, user)
            thisItem = getFileFromParent(db, parentBox, fileName, user)
        elif mode == 'l':
            modeName = 'link'
            fullPath = splitPathString(itemPathString)
            boxPath, linkName = fullPath[:-1], fullPath[-1]
            parentBox = getBoxFromPath(db, boxPath, user)
            thisItem = getLinkFromParent(db, parentBox, linkName, user)
        elif mode == 'u':
            modeName = 'user'
            parentBox = None
            thisItem = user
        elif mode == 'au':
            modeName = 'adminuser'
            if userIsAdmin(db, user):
                thisItem = dbGetUser(db, itemPathString)
                parentBox = None
            else:
                raise OstracionError('Insufficient permissions')
        elif mode == 's':
            modeName = 'settingIcon'
            if userIsAdmin(db, user):
                settingGroupId, settingId = itemPathString.split('/')
                thisItem = g.settings['image'][settingGroupId][settingId]
                parentBox = None
            else:
                raise OstracionError('Insufficient permissions')
        else:
            raise RuntimeError('Unknown mode encountered')
        #
        storageSuccess = storeFileAsThumbnail(
            db,
            fileToSave=None,
            mode=mode,
            thumbnailFormat=determineThumbnailFormatByModeAndTarget(
                db,
                mode,
                thisItem,
            ),
            targetItem=thisItem,
            parentBox=parentBox,
            user=user,
            tempFileDirectory=tempFileDirectory,
            fileStorageDirectory=fileStorageDirectory,
        )
        if not storageSuccess:
            raise OstracionError('Could not unset the icon')
        #
        if mode in {'f', 'b', 'l'}:
            return redirect(url_for(
                'lsView',
                lsPathString='/'.join(
                    boxPath[1:-1] if mode == 'b' else boxPath[1:]
                ),
            ))
        elif mode == 'u':
            return redirect(url_for(
                'userProfileView',
            ))
        elif mode == 'au':
            return redirect(url_for(
                'adminHomeUsersView',
            ))
        elif mode == 's':
            return redirect(url_for(
                'adminHomeSettingsImagesView',
            ))
        else:
            raise RuntimeError('Unknown mode encountered')


@app.route('/seticon/<mode>/<path:itemPathString>', methods=['GET', 'POST'])
@app.route('/seticon/<mode>/', methods=['GET', 'POST'])
@app.route('/seticon/<mode>', methods=['GET', 'POST'])
def setIconView(mode, itemPathString=''):
    """ Route to set/replace the thumbnail of various items."""
    if (mode == 'au' and
            not g.settings['behaviour']['behaviour_admin_powers'][
                'admin_is_god']['value']):
        request._onErrorUrl = url_for('adminHomeUsersView')
        raise OstracionError('This feature is turned off in the configuration')
    else:
        user = g.user
        form = UploadIconForm()
        db = dbGetDatabase()
        tempFileDirectory = g.settings['system']['system_directories'][
            'temp_directory']['value']
        fileStorageDirectory = g.settings['system']['system_directories'][
            'fs_directory']['value']
        if mode == 'b':
            boxPath = splitPathString(itemPathString)
            request._onErrorUrl = url_for(
                'lsView',
                lsPathString='/'.join(boxPath[1:]),
            )
            parentBox = None
            thisItem = getBoxFromPath(db, boxPath, user)
            itemName = thisItem.getName()
            pageFeatures = {
                'breadCrumbs': makeBreadCrumbs(
                    splitPathString(itemPathString),
                    g,
                    appendedItems=[{
                        'kind': 'link',
                        'target': None,
                        'name': 'Icon',
                    }],
                ),
            }
        elif mode == 'f':
            fullPath = splitPathString(itemPathString)
            boxPath, fileName = fullPath[:-1], fullPath[-1]
            request._onErrorUrl = url_for(
                'lsView',
                lsPathString='/'.join(boxPath[1:]),
            )
            parentBox = getBoxFromPath(db, boxPath, user)
            thisItem = getFileFromParent(db, parentBox, fileName, user)
            itemName = thisItem.getName()
            pageFeatures = {
                'breadCrumbs': makeBreadCrumbs(
                    splitPathString(itemPathString)[:-1],
                    g,
                    appendedItems=[
                        {
                            'kind': 'file',
                            'target': thisItem,
                        },
                        {
                            'kind': 'link',
                            'target': None,
                            'name': 'Icon',
                        }
                    ],
                ),
            }
        elif mode == 'l':
            fullPath = splitPathString(itemPathString)
            boxPath, linkName = fullPath[:-1], fullPath[-1]
            request._onErrorUrl = url_for(
                'lsView',
                lsPathString='/'.join(boxPath[1:]),
            )
            parentBox = getBoxFromPath(db, boxPath, user)
            thisItem = getLinkFromParent(db, parentBox, linkName, user)
            itemName = thisItem.getName()
            pageFeatures = {
                'breadCrumbs': makeBreadCrumbs(
                    splitPathString(itemPathString)[:-1],
                    g,
                    appendedItems=[
                        {
                            'kind': 'external_link',
                            'target': thisItem,
                        },
                        {
                            'kind': 'link',
                            'target': None,
                            'name': 'Icon',
                        }
                    ],
                ),
            }
        elif mode == 'u':
            pageFeatures = prepareTaskPageFeatures(
                userProfilePageDescriptor,
                ['root', 'icon'],
                g,
                overrides={
                    'pageTitle': None,
                    'pageSubtitle': None,
                    'iconUrl': None,
                },
            )
            thisItem = user
            itemName = thisItem.getName()
            parentBox = None
        elif mode == 'au':
            pageFeatures = prepareTaskPageFeatures(
                adminPageDescriptor,
                ['root', 'users'],
                g,
                appendedItems=[
                    {
                        'kind': 'link',
                        'link': False,
                        'target': None,
                        'name': 'Icon',
                    }
                ],
                overrides={
                    'pageTitle': None,
                    'pageSubtitle': None,
                    'iconUrl': None,
                },
            )
            if userIsAdmin(db, user):
                thisItem = dbGetUser(db, itemPathString)
                itemName = thisItem.getName()
                parentBox = None
            else:
                raise OstracionError('Insufficient permissions')
        elif mode == 's':
            pageFeatures = prepareTaskPageFeatures(
                adminPageDescriptor,
                ['root', 'settings', 'images'],
                g,
                appendedItems=[
                    {
                        'kind': 'link',
                        'link': False,
                        'target': None,
                        'name': 'Set image',
                    }
                ],
                overrides={
                    'pageTitle': None,
                    'pageSubtitle': None,
                    'iconUrl': None,
                },
            )
            if userIsAdmin(db, user):
                settingGroupId, settingId = itemPathString.split('/')
                thisItem = g.settings['image'][settingGroupId][settingId]
                itemName = thisItem['setting'].getName()
                parentBox = None
            else:
                raise OstracionError('Insufficient permissions')
        else:
            raise RuntimeError('Unknown mode encountered')
        #
        if form.validate_on_submit():
            #
            storageSuccess = storeFileAsThumbnail(
                db,
                fileToSave=form.file.data,
                mode=mode,
                thumbnailFormat=determineThumbnailFormatByModeAndTarget(
                    db,
                    mode,
                    thisItem,
                ),
                targetItem=thisItem,
                parentBox=parentBox,
                user=user,
                tempFileDirectory=tempFileDirectory,
                fileStorageDirectory=fileStorageDirectory,
            )
            if not storageSuccess:
                raise OstracionError('Could not set the icon')
            #
            if mode in {'f', 'b', 'l'}:
                return redirect(url_for(
                    'lsView',
                    lsPathString='/'.join(
                        boxPath[1:-1] if mode == 'b' else boxPath[1:]
                    ),
                ))
            elif mode == 'u':
                return redirect(url_for(
                    'userProfileView',
                ))
            elif mode == 'au':
                return redirect(url_for(
                    'adminHomeUsersView',
                ))
            elif mode == 's':
                return redirect(url_for(
                    'adminHomeSettingsImagesView',
                ))
            else:
                raise RuntimeError('Unknown mode encountered')
        else:
            #
            titleMap = {
                'f': 'Set File Icon',
                'l': 'Set Link Icon',
                'b': 'Set Box Icon',
                'u': 'Set User Icon',
                'au': 'Set User Icon (as admin)',
                's': 'Set Application Image',
            }
            modeNameMap = {
                'f': 'for file',
                'l': 'for link',
                'b': 'for box',
                'u': 'for user',
                'au': '(as admin) for user',
                's': 'for setting',
            }
            finalPageFeatures = recursivelyMergeDictionaries(
                {
                    'pageTitle': titleMap[mode],
                    'pageSubtitle': 'Upload an image file %s "%s"' % (
                        modeNameMap[mode],
                        itemName,
                    ),
                },
                defaultMap=pageFeatures,
            )
            if mode == 'u':
                finalPageFeatures['iconUrl'] = url_for(
                    'userThumbnailView',
                    dummyId='%s_' % thisItem.icon_file_id,
                    username=thisItem.username,
                )
            elif mode == 'au':
                finalPageFeatures['iconUrl'] = url_for(
                    'userThumbnailView',
                    dummyId='%s_' % thisItem.icon_file_id,
                    username=thisItem.username,
                )
            elif mode == 's':
                finalPageFeatures['iconUrl'] = makeSettingImageUrl(
                    g,
                    settingGroupId,
                    settingId,
                )
            elif mode == 'b':
                finalPageFeatures['iconUrl'] = url_for(
                    'boxThumbnailView',
                    dummyId=thisItem.icon_file_id + '_',
                    boxPathString='/'.join(boxPath[1:]),
                )
            elif mode == 'f':
                finalPageFeatures['iconUrl'] = url_for(
                    'fileThumbnailView',
                    dummyId=thisItem.icon_file_id + '_',
                    fsPathString='/'.join(boxPath[1:] + [thisItem.name]),
                )
            elif mode == 'l':
                finalPageFeatures['iconUrl'] = url_for(
                    'linkThumbnailView',
                    dummyId=thisItem.icon_file_id + '_',
                    fsPathString='/'.join(boxPath[1:] + [thisItem.name]),
                )
            #
            return render_template(
                'uploadicon.html',
                form=form,
                user=user,
                mode=mode,
                itemPathString=itemPathString,
                **finalPageFeatures,
            )
