""" boxaccess.py
    Views to access boxes in various ways: ls, browse, tree view, etc.
"""

from datetime import datetime
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

from ostracion_app.utilities.tools.formatting import (
    formatBytesSize,
    applyDefault,
)

from ostracion_app.utilities.tools.setNaming import (
    colloquialJoinClauses,
    pickSingularPluralSentences,
)

from ostracion_app.app_main import app

from ostracion_app.utilities.viewTools.messageTools import flashMessage

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)
from ostracion_app.utilities.database.userTools import (
    dbGetUser,
)

from ostracion_app.utilities.database.fileSystem import (
    getBoxesFromParent,
    getBoxFromPath,
    makeBoxInParent,
    updateBox,
    deleteBox,
    getFilesFromBox,
    getLinksFromBox,
    getRootBox,
    isNameUnderParentBox,
    canDeleteBox,
    isAncestorBoxOf,
    moveBox,
)

from ostracion_app.utilities.viewTools.pathTools import (
    makeBreadCrumbs,
    splitPathString,
    prepareBoxActions,
    prepareFileActions,
    prepareLinkActions,
    prepareFileInfo,
    prepareLinkInfo,
    prepareBoxInfo,
    prepareBoxHeaderActions,
    prepareRootTasks,
    describePathAsNiceString,
)

from ostracion_app.utilities.forms.forms import (
    makeMakeBoxForm,
    generateFsTicketForm,
)

from ostracion_app.utilities.tools.treeTools import (
    getMaxTreeDepth,
    collectTreeFromBox,
    treeAny,
)

from ostracion_app.utilities.database.permissions import (
    userIsAdmin,
    userRoleRequired,
    userHasPermission,
    calculateBoxPermissionAlgebra,
    dbInsertBoxRolePermission,
)

from ostracion_app.utilities.fileIO.physical import (
    flushFsDeleteQueue,
)

from ostracion_app.utilities.models.Box import Box
from ostracion_app.utilities.models.BoxRolePermission import BoxRolePermission

from ostracion_app.utilities.database.settingsTools import (
    makeSettingImageUrl,
)

from ostracion_app.utilities.tools.colorTools import (
    prepareColorShadeMap,
)

from ostracion_app.utilities.database.tickets import (
    dbMakeUploadTicket,
    dbMakeGalleryTicket,
)

from ostracion_app.utilities.viewTools.pathTools import (
    prepareTaskPageFeatures,
)

from ostracion_app.views.viewTools.toolsPageTreeDescriptor import (
    toolsPageDescriptor,
)


@app.route('/ls')
@app.route('/ls/')
@app.route('/ls/<path:lsPathString>')
def lsView(lsPathString=''):
    """LS-of-a-box route, additionally with 'tasks' if viewing root."""
    user = g.user
    lsPath = splitPathString(lsPathString)
    db = dbGetDatabase()
    thisBox = getBoxFromPath(db, lsPath, user)
    boxPath = lsPath[1:]
    #
    showBoxPermissionToAll = g.settings['behaviour']['behaviour_permissions'][
        'show_permission']['value']
    #
    if thisBox is not None:
        request._onErrorUrl = url_for('lsView')
        if thisBox.box_id == '':
            tasks = prepareRootTasks(db, g, user)
        else:
            tasks = []
        boxes = [
            {
                'box': box,
                'path': boxPath + [box.box_name],
                'info': prepareBoxInfo(db, box),
                'actions': prepareBoxActions(
                    db,
                    box,
                    boxPath + [box.box_name],
                    thisBox,
                    user
                ),
            }
            for box in sorted(
                (
                    b
                    for b in getBoxesFromParent(db, thisBox, user)
                    if b is not None
                ),
                key=lambda b: (b.box_name.lower(), b.box_name),
            )
            if box.box_id != ''
        ]
        files = [
            {
                'file': file,
                'path': boxPath + [file.name],
                'nice_size': formatBytesSize(file.size),
                'info': prepareFileInfo(db, file),
                'actions': prepareFileActions(
                    db,
                    file,
                    boxPath + [file.name],
                    thisBox,
                    user
                ),
            }
            for file in sorted(
                getFilesFromBox(db, thisBox),
                key=lambda f: (f.name.lower(), f.name),
            )
        ]
        links = [
            {
                'link': link,
                'path': boxPath + [link.name],
                'info': prepareLinkInfo(db, link),
                'actions': prepareLinkActions(
                    db,
                    link,
                    boxPath + [link.name],
                    thisBox,
                    user
                ),
            }
            for link in sorted(
                getLinksFromBox(db, thisBox),
                key=lambda l: (l.name.lower(), l.name),
            )
        ]
        #
        pathBCrumbs = makeBreadCrumbs(lsPath, g)
        boxNiceName = thisBox.box_name if thisBox.box_name != '' else None
        #
        boxActions = prepareBoxHeaderActions(
            db,
            thisBox,
            boxPath,
            user,
            discardedActions=(
                set()
                if len(files) > 0
                else {'gallery_view', 'issue_gallery_ticket'}
            ),
        )
        showAdminToolsLink = userIsAdmin(db, user)
        if showBoxPermissionToAll or userIsAdmin(db, user):
            thisBoxPermissionAlgebra = calculateBoxPermissionAlgebra(
                thisBox.permissionHistory,
                thisBox.permissions,
            )
            permissionInfo = {
                'powers': {
                    powK: [
                        '+'.join(sorted(st))
                        for st in thisBoxPermissionAlgebra[powK]
                    ]
                    for powK in {'r', 'w', 'c'}
                },
                'assignments': {
                    'edit_url': (
                        url_for(
                            'adminLsPermissionsView',
                            lsPathString='/'.join(boxPath),
                        )
                        if showAdminToolsLink
                        else None
                    ),
                    'native': [
                        {
                            'role_id': brp.role_id,
                            'r': brp.r,
                            'w': brp.w,
                            'c': brp.c,
                        }
                        for brp in sorted(thisBox.listPermissions('native'))
                    ],
                    'inherited': [
                        {
                            'role_id': brp.role_id,
                            'r': brp.r,
                            'w': brp.w,
                            'c': brp.c,
                        }
                        for brp in sorted(thisBox.listPermissions('inherited'))
                    ],
                },
            }
        else:
            permissionInfo = None
        #
        if len(boxes) + len(files) + len(links) > 0:
            foundCounts = [
                (len(boxes), 'box', 'boxes'),
                (len(files), 'file', 'files'),
                (len(links), 'link', 'links'),
            ]
            foundParts = pickSingularPluralSentences(
                foundCounts,
                keepZeroes=False,
            )
            boxChildrenCounter = colloquialJoinClauses(foundParts)
        else:
            boxChildrenCounter = 'no contents'
        #
        return render_template(
            'ls.html',
            user=user,
            thisBox=thisBox,
            boxNiceName=boxNiceName,
            pageTitle=boxNiceName,
            boxChildrenCounter=boxChildrenCounter,
            boxActions=boxActions,
            boxPath=boxPath,
            permissionInfo=permissionInfo,
            breadCrumbs=pathBCrumbs,
            tasks=tasks,
            boxes=boxes,
            files=files,
            links=links,
        )
    else:
        request._onErrorUrl = url_for(
            'lsView',
            lsPathString='/'.join(lsPath[1:-1]),
        )
        raise OstracionWarning(
            'Cannot access the specified box "%s"' % lsPath[-1]
        )


@app.route('/mkbox', methods=['GET', 'POST'])
@app.route('/mkbox/', methods=['GET', 'POST'])
@app.route('/mkbox/<path:parentBoxPathString>', methods=['GET', 'POST'])
def makeBoxView(parentBoxPathString=''):
    """MKBOX-in-a-box- route."""
    user = g.user
    form = makeMakeBoxForm('Create')()
    db = dbGetDatabase()
    parentBoxPath = splitPathString(parentBoxPathString)
    parentBox = getBoxFromPath(db, parentBoxPath, user)
    boxNiceName = parentBox.box_name if parentBox.box_name != '' else '(root)'
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(parentBoxPath),
    )
    if form.validate_on_submit():
        #
        boxName = form.boxname.data
        boxDescription = form.boxdescription.data
        boxTitle = form.boxtitle.data
        #
        newBox = Box(
            box_name=boxName,
            title=boxTitle,
            description=boxDescription,
            icon_file_id='',
            nature='box',
            parent_id=parentBox.box_id,
            date=datetime.now(),
            creator_username=user.username,
            icon_file_id_username=user.username,
            metadata_username=user.username,
        )
        makeBoxInParent(db, parentBox, newBox, user, skipCommit=True)
        if parentBox.box_id == '':
            # the new box is a direct child of root:
            # act according to the localhost-mode policy setting
            rootChildAnonPerms = g.settings['behaviour'][
                'behaviour_permissions'][
                'rootchild_box_anonymous_permissions']['value']
            rcPermSet = {
                k: 1 if rootChildAnonPerms[i] != '_' else 0
                for i, k in enumerate('rwc')
            }
            # the above is a bit of a hack which parses the char
            # of the setting 'r__', 'rwc', ...
            rootChildBRP = BoxRolePermission(
                box_id=newBox.box_id,
                role_id='anonymous',
                **rcPermSet,
            )
            dbInsertBoxRolePermission(
                db,
                rootChildBRP,
                user,
                skipCommit=True,
            )
        #
        db.commit()
        additionalLsItems = [boxName]
        #
        return redirect(url_for(
            'lsView',
            lsPathString='/'.join(parentBoxPath[1:] + additionalLsItems),
        ))
    else:
        pathBCrumbs = makeBreadCrumbs(
            parentBoxPath,
            g,
            appendedItems=[{
                'kind': 'link',
                'target': None,
                'name': 'Make box',
            }],
        )
        return render_template(
            'makebox.html',
            form=form,
            user=user,
            breadCrumbs=pathBCrumbs,
            iconUrl=makeSettingImageUrl(g, 'app_images', 'standard_box'),
            pageTitle='Create box in "%s"' % boxNiceName,
            pageSubtitle='Name and title are mandatory',
        )


@app.route('/rmbox')
@app.route('/rmbox/')
@app.route('/rmbox/<path:boxPathString>')
def deleteBoxView(boxPathString=''):
    """RMBOX route."""
    user = g.user
    db = dbGetDatabase()
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    boxPath = splitPathString(boxPathString)
    box = getBoxFromPath(db, boxPath, user)
    parentBox = getBoxFromPath(db, boxPath[:-1], user)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:-1]),
    )
    #
    canDelete = canDeleteBox(db, box, parentBox, user)
    #
    if canDelete:
        if parentBox is None:
            # deletee box was root
            raise OstracionError('Cannot act on this object')
        else:
            if box is not None:
                fsDeleteQueue = deleteBox(
                    db,
                    box,
                    parentBox,
                    user,
                    fileStorageDirectory=fileStorageDirectory,
                )
                flushFsDeleteQueue(fsDeleteQueue)
            else:
                raise OstracionError('Box not accessible')
    else:
        raise OstracionError('Cannot delete this box')
    return redirect(url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:-1]),
    ))


@app.route('/mdbox', methods=['GET', 'POST'])
@app.route('/mdbox/', methods=['GET', 'POST'])
@app.route('/mdbox/<path:boxPathString>', methods=['GET', 'POST'])
def metadataBoxView(boxPathString=''):
    """edit-metadata-of-box route."""
    user = g.user
    db = dbGetDatabase()
    boxPath = splitPathString(boxPathString)
    box = getBoxFromPath(db, boxPath, user)
    parentBox = getBoxFromPath(db, boxPath[:-1], user)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:-1]),
    )
    #
    form = makeMakeBoxForm('Save')()
    if parentBox is None:
        # target box was root
        raise OstracionError('Cannot act on this object')
    else:
        if box is not None:
            #
            if form.validate_on_submit():
                newBox = Box(
                    **recursivelyMergeDictionaries(
                        {
                            'box_name': form.boxname.data,
                            'title': form.boxtitle.data,
                            'description': form.boxdescription.data,
                            'metadata_username': (
                                user.username
                                if user.is_authenticated
                                else ''
                            ),
                        },
                        defaultMap=box.asDict(),
                    )
                )
                updateBox(db, boxPath, newBox, user)
                return redirect(url_for(
                    'lsView',
                    lsPathString='/'.join(boxPath[1:-1]),
                ))
            else:
                form.boxname.data = applyDefault(
                    form.boxname.data,
                    box.box_name,
                )
                form.boxdescription.data = applyDefault(
                    form.boxdescription.data,
                    box.description,
                )
                form.boxtitle.data = applyDefault(
                    form.boxtitle.data,
                    box.title,
                )
                pathBCrumbs = makeBreadCrumbs(
                    boxPath,
                    g,
                    appendedItems=[{
                        'kind': 'link',
                        'target': None,
                        'name': 'Metadata',
                    }],
                )
                return render_template(
                    'makebox.html',
                    form=form,
                    user=user,
                    breadCrumbs=pathBCrumbs,
                    pageTitle='Edit box metadata',
                    pageSubtitle='Name and title are mandatory',
                    iconUrl=url_for(
                        'boxThumbnailView',
                        dummyId=box.icon_file_id + '_',
                        boxPathString='/'.join(boxPath[1:]),
                    ),
                )
            #
        else:
            raise OstracionWarning('Box not accessible')
    return redirect(url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:-1]),
    ))


@app.route('/dirtreeview')
@app.route('/dirtreeview/<int:includeFiles>')
def dirTreeView(includeFiles=0):
    """ Box-tree route.
        Can show files or not depending of optional parameter 'includeFiles'
        and the availability of files as configured in settings.
    """
    user = g.user
    db = dbGetDatabase()
    #
    if not g.canShowTreeView:
        raise OstracionError('Insufficient permissions')
    #
    canIncludeFiles = g.settings['behaviour']['search'][
        'tree_view_files_visible']['value']
    if not canIncludeFiles:
        includeFiles = 0
    availableViewModes = [0] + ([1] if canIncludeFiles else [])
    viewModeActions = {}
    if len(availableViewModes) > 1:
        if includeFiles == 0:
            viewModeActions['disabled_hide_tree_files'] = 'yes'
        else:
            viewModeActions['hide_tree_files'] = url_for(
                'dirTreeView',
                includeFiles=0,
            )
        if includeFiles != 0:
            viewModeActions['disabled_show_tree_files'] = 'yes'
        else:
            viewModeActions['show_tree_files'] = url_for(
                'dirTreeView',
                includeFiles=1,
            )
    else:
        raise NotImplementedError('no available view modes in dirTreeView')
    #
    rootBox = getRootBox(db)
    tree = collectTreeFromBox(db, rootBox, user, includeFiles != 0)
    #
    maxDepth = getMaxTreeDepth(tree)
    if includeFiles:
        gradientDestinationColor = g.settings['color']['tree_shade_colors'][
            'shade_treeview_files']['value']
    else:
        gradientDestinationColor = g.settings['color']['tree_shade_colors'][
            'shade_treeview_boxes']['value']
    #
    colorShadeMap = prepareColorShadeMap(
        g.settings['color']['navigation_colors']['box']['value'],
        gradientDestinationColor,
        numShades=1 + maxDepth,
    )
    #
    pageFeatures = prepareTaskPageFeatures(
        toolsPageDescriptor,
        ['root', 'tree_view'],
        g,
    )
    #
    return render_template(
        'dirtreeview.html',
        tree=tree,
        mode='tree_view',
        colorShadeMap=colorShadeMap,
        user=user,
        actions=viewModeActions,
        **pageFeatures,
    )


@app.route('/makegalleryticketbox', methods=['GET', 'POST'])
@app.route('/makegalleryticketbox/', methods=['GET', 'POST'])
@app.route(
    '/makegalleryticketbox/<path:boxPathString>',
    methods=['GET', 'POST'],
)
@userRoleRequired({'admin', 'ticketer'})
def makeTicketBoxGalleryView(boxPathString=''):
    """Make-gallery-ticket-of-box route."""
    user = g.user
    db = dbGetDatabase()
    boxPath = splitPathString(boxPathString)
    box = getBoxFromPath(db, boxPath, user)
    request._onErrorUrl = url_for('lsView', lsPathString='/'.join(boxPath[1:]))
    #
    pathBCrumbs = makeBreadCrumbs(
        boxPath,
        g,
        appendedItems=[
            {
                'name': '(create gallery ticket)',
                'kind': 'link',
                'target': url_for(
                    'makeTicketBoxGalleryView',
                    boxPathString=boxPathString,
                ),
                'link': False,
            },
        ],
    )
    form = generateFsTicketForm(
        fileModePresent=False,
        settings=g.settings,
    )
    if form.validate_on_submit():
        magicLink = dbMakeGalleryTicket(
            db=db,
            ticketName=form.name.data,
            validityHours=(int(form.validityhours.data)
                           if form.validityhours.data != ''
                           else None),
            multiplicity=(int(form.multiplicity.data)
                          if form.multiplicity.data != ''
                          else None),
            ticketMessage=(form.ticketmessage.data
                           if form.ticketmessage.data != ''
                           else None),
            box=box,
            boxPath=boxPath,
            user=user,
            urlRoot=request.url_root,
            settings=g.settings,
        )
        flashMessage(
            'Success',
            'Done',
            ('Gallery ticket generated. Give the recipient '
             'the following magic link:'),
            pillText=magicLink,
        )
        return redirect(url_for(
            'lsView',
            lsPathString='/'.join(boxPath[1:]),
        ))
    else:
        defaultName = 'Gallery-View-%s' % (
            box.box_name if box.box_name != '' else '(root)',
        )
        form.name.data = applyDefault(form.name.data, defaultName)
        form.ticketmessage.data = applyDefault(
            form.ticketmessage.data,
            'Please, look at this gallery',
        )
        maxValidityHours = g.settings['behaviour']['behaviour_tickets'][
            'max_ticket_validityhours']['value']
        form.validityhours.data = applyDefault(
            form.validityhours.data,
            str(maxValidityHours) if maxValidityHours is not None else '',
        )
        maxMultiplicity = g.settings['behaviour']['behaviour_tickets'][
            'max_ticket_multiplicity']['value']
        form.multiplicity.data = applyDefault(
            form.multiplicity.data,
            str(maxMultiplicity) if maxMultiplicity is not None else '',
        )
        return render_template(
            'fsticket.html',
            pageTitle='Create public gallery-view ticket',
            pageSubtitle=('Recipient(s) of the ticket will be able to view '
                          'files (and not contained boxes) in "%s", without '
                          'an account, as a gallery. If setting a number of '
                          'accesses, keep in mind that every single-file view'
                          ' counts toward the total accesses.') % (
                boxPathString if boxPathString != '' else '(root)',
            ),
            baseMultiplicityCaption='Number of granted accesses',
            user=user,
            form=form,
            iconUrl=makeSettingImageUrl(g, 'app_images', 'gallery_ticket'),
            showFileMode=False,
            breadCrumbs=pathBCrumbs,
        )


@app.route('/maketicketboxuploadview', methods=['GET', 'POST'])
@app.route('/maketicketboxuploadview/', methods=['GET', 'POST'])
@app.route(
    '/maketicketboxuploadview/<path:boxPathString>',
    methods=['GET', 'POST'],
)
@userRoleRequired({'admin', 'ticketer'})
def makeTicketBoxUploadView(boxPathString=''):
    """Make-upload-ticket (to a box) route."""
    user = g.user
    db = dbGetDatabase()
    boxPath = splitPathString(boxPathString)
    box = getBoxFromPath(db, boxPath, user)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    #
    if userHasPermission(db, user, box.permissions, 'w'):
        #
        pathBCrumbs = makeBreadCrumbs(
            boxPath,
            g,
            appendedItems=[
                {
                    'name': '(create upload ticket)',
                    'kind': 'link',
                    'target': url_for(
                        'makeTicketBoxUploadView',
                        boxPathString=boxPathString,
                    ),
                    'link': False,
                },
            ],
        )
        form = generateFsTicketForm(
            fileModePresent=False,
            settings=g.settings,
        )
        if form.validate_on_submit():
            magicLink = dbMakeUploadTicket(
                db=db,
                ticketName=form.name.data,
                validityHours=(int(form.validityhours.data)
                               if form.validityhours.data != ''
                               else None),
                multiplicity=(int(form.multiplicity.data)
                              if form.multiplicity.data != ''
                              else None),
                ticketMessage=(form.ticketmessage.data
                               if form.ticketmessage.data != ''
                               else None),
                box=box,
                boxPath=boxPath,
                user=user,
                urlRoot=request.url_root,
                settings=g.settings,
            )
            flashMessage(
                'Success',
                'Done',
                ('Upload ticket generated. Give the recipient '
                 'the following magic link:'),
                pillText=magicLink,
            )
            return redirect(url_for(
                'lsView',
                lsPathString='/'.join(boxPath[1:]),
            ))
        else:
            defaultName = 'Upload-To-%s' % (
                box.box_name if box.box_name != '' else '(root)',
            )
            form.name.data = applyDefault(form.name.data, defaultName)
            form.ticketmessage.data = applyDefault(
                form.ticketmessage.data,
                'Please, upload files to this box',
            )
            maxValidityHours = g.settings['behaviour']['behaviour_tickets'][
                'max_ticket_validityhours']['value']
            form.validityhours.data = applyDefault(
                form.validityhours.data,
                str(maxValidityHours) if maxValidityHours is not None else '',
            )
            maxMultiplicity = g.settings['behaviour']['behaviour_tickets'][
                'max_ticket_multiplicity']['value']
            form.multiplicity.data = applyDefault(
                form.multiplicity.data,
                str(maxMultiplicity) if maxMultiplicity is not None else '',
            )
            return render_template(
                'fsticket.html',
                pageTitle='Create public upload ticket',
                pageSubtitle=('Recipient(s) of the ticket will be able to '
                              'upload to "%s", without an account, on '
                              'your behalf.') % (
                                    boxPathString
                                    if boxPathString != ''
                                    else '(root)'),
                baseMultiplicityCaption='Number of granted file uploads',
                user=user,
                form=form,
                iconUrl=makeSettingImageUrl(g, 'app_images', 'upload_ticket'),
                showFileMode=False,
                breadCrumbs=pathBCrumbs,
            )
        #
    else:
        raise OstracionError('Insufficient permissions')


@app.route('/mvbox/<quotedSrcBox>')
def fsMoveBoxView(quotedSrcBox):
    """
        Move-box-phase-1 route: where the source box is selected
        (and then in offering the choose-dest-box it is put in the URL
        for calling phase two).
    """
    user = g.user
    db = dbGetDatabase()
    # first we find the box
    bxPathString = urllib.parse.unquote_plus(quotedSrcBox)
    boxPath = splitPathString(bxPathString)
    parentBox = getBoxFromPath(db, boxPath[:-1], user)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:-1]),
    )
    box = getBoxFromPath(db, boxPath, user)
    if not canDeleteBox(db, box, parentBox, user):
        raise OstracionWarning('Cannot act on this object')
    # next we prepare the selectable destinations
    rootBox = getRootBox(db)

    def rbPredicate(richBox, _box=box, _srcBox=parentBox):
        _dstBox = richBox['box']
        if _box.parent_id != _dstBox.box_id:
            if all(userHasPermission(db, user, _dstBox.permissions, prm)
                    for prm in {'w', 'c'}):
                if not isNameUnderParentBox(db, _dstBox, _box.box_name):
                    if not isAncestorBoxOf(db, _box, _dstBox):
                        return True
        return False

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
        g.settings['color']['navigation_colors']['box']['value'],
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
        mode='box_move',
        object_quoted_path=quotedSrcBox,
        colorShadeMap=colorShadeMap,
        user=user,
        iconUrl=makeSettingImageUrl(g, 'app_images', 'move'),
        pageTitle='Select box destination',
        pageSubtitle=('Choose the box to which box "%s" '
                      'shall be moved from "%s"') % (
                            box.box_name,
                            describePathAsNiceString(boxPath[1:-1]),
                     ),
        actions=None,
        backToUrl=(None
                   if destinationsExist
                   else url_for(
                        'lsView',
                        lsPathString='/'.join(boxPath[1:]))),
        breadCrumbs=makeBreadCrumbs(
            boxPath,
            g,
            appendedItems=[
                {
                    'kind': 'link',
                    'target': None,
                    'name': 'Move box',
                }
            ],
        ),
    )


@app.route('/domvbox/<quotedSrcBox>/<quotedDestBox>')
@app.route('/domvbox/<quotedSrcBox>/')
@app.route('/domvbox/<quotedSrcBox>')
def fsDoMoveBoxView(quotedSrcBox, quotedDestBox=''):
    """
        Move-box-phase-2 route: where, with source and dest
        boxes as quoted-plus strings, the actual moving
        is performed.
    """
    user = g.user
    db = dbGetDatabase()
    # we retrieve the source box, its current parent
    # and the destination box
    srcBoxPathString = urllib.parse.unquote_plus(quotedSrcBox)
    srcBoxPath = splitPathString(srcBoxPathString)
    box = getBoxFromPath(db, srcBoxPath, user)
    srcBox = getBoxFromPath(db, srcBoxPath[:-1], user)
    dstBoxPathString = urllib.parse.unquote_plus(quotedDestBox)
    dstBoxPath = splitPathString(dstBoxPathString)
    dstBox = getBoxFromPath(db, dstBoxPath, user)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(srcBoxPath[1:-1]),
    )
    # we attempt the move
    moveBox(
        db,
        box,
        srcBox,
        dstBox,
        user,
    )
    return redirect(url_for(
        'lsView',
        lsPathString='/'.join(dstBoxPath[1:]),
    ))
