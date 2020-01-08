""" pathTools.py
    path-based utilities for views:
        - splitting of path strings into components
        - breadcrumbs for fs navigation
        - fixed special navigation structures (e.g. admin area)
        - calculation of set of action-buttons for files, boxes...
"""

import urllib.parse

from flask import (
    url_for,
)

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries,
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.database.permissions import (
    userHasPermission,
    userHasRole,
    userIsAdmin,
)

from ostracion_app.utilities.fileIO.fileTypes import (
    isFileViewable,
    isFileTextEditable,
)

from ostracion_app.utilities.database.userTools import (
    getUserFullName,
)

from ostracion_app.utilities.database.settingsTools import (
    makeSettingImageUrl,
)

from ostracion_app.utilities.database.fileSystem import (
    canDeleteBox,
)

from ostracion_app.views.viewTools.pageTreeDescriptorTools import (
    extractTopLevelTaskFromTreeDescriptor,
)

from ostracion_app.views.viewTools.toolsPageTreeDescriptor import (
    toolsPageDescriptor,
)

from ostracion_app.views.viewTools.infoPageTreeDescriptor import (
    infoPageDescriptor,
)

from ostracion_app.views.viewTools.adminPageTreeDescriptor import (
    adminPageDescriptor,
)

from ostracion_app.views.viewTools.userProfilePageTreeDescriptor import (
    userProfilePageDescriptor,
    userProfileTitler,
    userProfileSubtitler,
    userProfileThumbnailer,
)

from ostracion_app.views.viewTools.loginTools import (
    loginTitle,
    loginSubtitle,
    logoutTitle,
    logoutSubtitle,
)


def makeBreadCrumbs(lsPath, g, appendedItems=[]):
    """ Given a path and possibly some special items to append at the end,
        compute breadcrumbs.
    """
    bc = []
    rootAsIcon = True
    # ** Alternatively (to keep the '(root)' form when navbar visible): **
    # rootAsIcon = g.settings['behaviour']['behaviour_appearance'][
    #     'hide_navbar']['value']
    collectedPath = []
    for itmIndex, itm in enumerate(lsPath):
        collectedPath.append(itm)
        bc.append(
            {
                'name': itm if itm != '' else '(root)',
                'type': 'box',
                'target': url_for(
                    'lsView',
                    lsPathString='/'.join([pi for pi in collectedPath[1:]])
                ),
                'link': (len(appendedItems) > 0 or
                         itmIndex + 1 != len(lsPath)),
                'is_root_as_pic': itm == '' and rootAsIcon,
            }
        )
    for aiIndex, appendedItem in enumerate(appendedItems):
        bc.append(formatAppendedBreadcrumbItem(
            appendedItem,
            aiIndex + 1 != len(appendedItems),
            collectedFsPath=collectedPath,
        ))
    #
    return bc


def describePathAsNiceString(pth):
    """Reformat a path to cover the only-root case gracefully."""
    if len(pth) == 0:
        return '(Root)'
    else:
        return '/%s' % ('/'.join(pth))


def collectAlongDescriptorTree(pDesc, pPath, collected=[]):
    """ Perform a single step in browsing a descriptor
        tree to make up desctree-based breadcrumbs."""
    if len(pPath) == 0:
        return collected, pDesc
    else:
        pItem = pPath[0]
        leftoverPath = pPath[1:]
        newDesc = pDesc['tasks'][pItem]
        return collectAlongDescriptorTree(
            newDesc,
            leftoverPath,
            collected + [{k: v for k, v in pDesc.items() if k != 'tasks'}],
        )


def formatAppendedBreadcrumbItem(appendedItem, hasLink, collectedFsPath=None):
    """ Prepare a breadcrumb item for display
        based on internal prescriptions.
    """
    if appendedItem['kind'] == 'file':
        return {
            'name': appendedItem['target'].name,
            'type': appendedItem['kind'],
            'target': url_for(
                'fsView',
                fsPathString='/'.join(
                    collectedFsPath[1:]+[appendedItem['target'].name]
                ),
            ),
            'link': hasLink,
        }
    elif appendedItem['kind'] == 'external_link':
        return {
            'name': appendedItem['target'].name,
            'type': appendedItem['kind'],
            'target': appendedItem['target'].target,
            'link': True,
        }
    elif appendedItem['kind'] == 'link':
        return {
            'name': appendedItem['name'],
            'type': appendedItem['kind'],
            'target': appendedItem['target'],
            'link': hasLink,
        }
    else:
        raise NotImplementedError('unknown appendedItem kind')


def prepareTaskPageFeatures(pageDescriptor, pagePath, g, appendedItems=[],
                            overrides={}):
    """ Calculate a dictionary with standard features for
        render_template'ing of special pages.

        Return a dict with:
            iconUrl,
            pageTitle,
            pageSubtitle,
            tasks,
            breadCrumbs
        for use in rendering templates of pages.

        pagePath is e.g. ['root','users']
            (must start with 'root')

        This is done with standard titling and navigation
        (e.g. admin-page nodes or a leaf item in the tree (no tasks)).

        One can pass overrides to customize parts of the prepared features.
    """
    bcPages, thisPage = collectAlongDescriptorTree(pageDescriptor, pagePath)
    # bcPages must be taken as [1:]
    # and thisPage is the inert part of the bcrumb
    # we add the 'root' starting point to all responses
    rootAsIcon = True
    # ** Alternatively (to keep the '(root)' form when navbar visible): **
    # rootAsIcon = g.settings['behaviour']['behaviour_appearance'][
    #     'hide_navbar']['value']
    breadCrumbs = [
        {
            'name': '(root)',
            'type': 'box',
            'target': url_for('lsView'),
            'link': True,
            'is_root_as_pic': rootAsIcon,
        }
    ] + [
        {
            'name': bcP['title'],
            'type': 'link',
            'target': url_for(
                bcP['endpoint_name'][0],
                **bcP['endpoint_name'][1]
            ),
            'link': True,
        }
        for bcP in bcPages[1:]
    ] + [
        {
            'name': thisPage['title'],
            'type': 'link',
            'target': url_for(
                thisPage['endpoint_name'][0],
                **thisPage['endpoint_name'][1]
            ),
            'link': len(appendedItems) > 0,
        }
    ] + [
        formatAppendedBreadcrumbItem(
            appendedItem,
            hasLink=(appendedItemIndex + 1) != len(appendedItems),
        )
        for appendedItemIndex, appendedItem in enumerate(appendedItems)
    ]
    if thisPage['image_id'] is None:
        iconUrl = None
    else:
        iconUrl = makeSettingImageUrl(
            g,
            thisPage['image_id'][0],
            thisPage['image_id'][1],
        )
    pageTitle, pageSubtitle = thisPage['title'], thisPage['subtitle']
    if 'tasks' not in thisPage:
        tasks = None
    else:
        tasks = [
            {
                'url': url_for(
                    thisPage['tasks'][taskId]['endpoint_name'][0],
                    **thisPage['tasks'][taskId]['endpoint_name'][1],
                ),
                'name':         thisPage['tasks'][taskId]['title'],
                'description':  thisPage['tasks'][taskId]['subtitle'],
                'thumbnail':    makeSettingImageUrl(
                    g,
                    thisPage['tasks'][taskId]['image_id'][0],
                    thisPage['tasks'][taskId]['image_id'][1],
                ),
            }
            # ** this is left out: we expect 'task_order' to always exist **
            # for taskId in thisPage.get(
            #     'task_order',
            #     sorted(thisPage['tasks'].keys())
            # )
            for taskId in thisPage['task_order']
            if taskId in thisPage['tasks']
        ]
    #
    return {
        k: v
        for k, v in recursivelyMergeDictionaries(
            overrides,
            defaultMap={
                'iconUrl': iconUrl,
                'pageTitle': pageTitle,
                'pageSubtitle': pageSubtitle,
                'tasks': tasks,
                'breadCrumbs': breadCrumbs,
            },
        ).items()
        if v is not None
    }


def splitPathString(ps):
    """ Split a path from a string to an array,
        taking care of the leading root.
    """
    return [''] + [
        pItm.strip()
        for pItm in ps.split('/')
        if pItm.strip() != ''
    ]


def prepareBoxInfo(db, box):
    """Calculate box information for display."""
    return [
        {
            'action': 'Created',
            'actor': getUserFullName(db, box.creator_username),
        },
        {
            'action': 'Icon',
            'actor': getUserFullName(db, box.icon_file_id_username),
        },
        {
            'action': 'Metadata',
            'actor': getUserFullName(db, box.metadata_username),
        },
    ]


def prepareBoxHeaderActions(db, box, boxPath, user, discardedActions=set()):
    """ According to the user's power on a box, calculate
        the available actions for the heading of the box view.
    """
    ticketerOrAdmin = (userHasRole(db, user, 'ticketer') or
                       userIsAdmin(db, user))
    canWriteFiles = userHasPermission(db, user, box.permissions, 'w')
    canChangeBoxes = userHasPermission(db, user, box.permissions, 'c')
    canIssueUploadTicket = ((canWriteFiles and ticketerOrAdmin) or
                            userIsAdmin(db, user))
    canIssueGalleryTicket = ticketerOrAdmin
    boxActions = {
        'mkbox': url_for(
            'makeBoxView',
            parentBoxPathString='/'.join(boxPath),
        ) if canChangeBoxes else None,
        'upload_single': url_for(
            'uploadSingleFileView',
            fsPathString='/'.join(boxPath),
        ) if canWriteFiles else None,
        'upload_multiple': url_for(
            'uploadMultipleFilesView',
            fsPathString='/'.join(boxPath)
        ) if canWriteFiles else None,
        'make_text': url_for(
            'makeTextFileView',
            fsPathString='/'.join(boxPath)
        ) if canWriteFiles else None,
        'make_link': url_for(
            'makeLinkView',
            fsPathString='/'.join(boxPath)
        ) if canWriteFiles else None,
        'issue_upload_ticket': url_for(
            'makeTicketBoxUploadView',
            boxPathString='/'.join(boxPath)
        ) if canIssueUploadTicket else None,
        'gallery_view': url_for(
            'fsGalleryView',
            fsPathString='/'.join(boxPath)
        ),
        'issue_gallery_ticket': url_for(
            'makeTicketBoxGalleryView',
            boxPathString='/'.join(boxPath)
        ) if canIssueGalleryTicket else None,
    }
    return {
        k: v
        for k, v in boxActions.items()
        if v is not None
        if k not in discardedActions
    }


def prepareBoxActions(db, box, boxPath, parentBox,
                      user, prepareParentButton=False):
    """ Prepare the list of actions available for the
        box to the user in the UI
        for use in the box-as-item view (i.e. ls).
    """
    bActions = {}
    # delete
    if canDeleteBox(db, box, parentBox, user):
        bActions['delete'] = url_for(
            'deleteBoxView',
            boxPathString='/'.join(boxPath),
        )
        bActions['move'] = url_for(
            'fsMoveBoxView',
            quotedSrcBox=urllib.parse.quote_plus('/'.join(boxPath)),
        )
    # change icon
    if userHasPermission(db, user, box.permissions, 'w'):
        bActions['icon'] = url_for(
            'setIconView',
            mode='b',
            itemPathString='/'.join(boxPath),
        )
    if userHasPermission(db, user, box.permissions, 'w'):
        bActions['metadata'] = url_for(
            'metadataBoxView',
            boxPathString='/'.join(boxPath),
        )
    #
    if prepareParentButton:
        bActions['parent'] = url_for(
            'lsView',
            lsPathString='/'.join(boxPath[:-1]),
        )
    #
    return bActions


def prepareFileInfo(db, file):
    """Calculate file information for display."""
    return [
        infoItem
        for infoItem in (
            {
                'action': 'Created',
                'actor': getUserFullName(db, file.creator_username),
            },
            {
                'action': 'Last edited',
                'actor': (getUserFullName(db, file.editor_username)
                          if file.creator_username != file.editor_username
                          else None),
            },
            {
                'action': 'Icon',
                'actor': getUserFullName(db, file.icon_file_id_username),
            },
            {
                'action': 'Metadata',
                'actor': getUserFullName(db, file.metadata_username),
            },
        )
        if infoItem['actor'] is not None
    ]


def prepareLinkActions(db, link, linkPath, parentBox, user,
                       discardedActions=set(), prepareParentButton=False):
    """ Calculate the actions on a link available to user (according to their
        powers) for showing in the link-as-ls-item view.
    """
    lActions = {}
    # active stuff
    if userHasPermission(db, user, parentBox. permissions, 'w'):
        lActions['icon'] = url_for(
            'setIconView',
            mode='l',
            itemPathString='/'.join(linkPath),
        )
        lActions['metadata'] = url_for(
            'fsMetadataView',
            fsPathString='/'.join(linkPath),
        )
        lActions['delete'] = url_for(
            'fsDeleteFileView',
            fsPathString='/'.join(linkPath),
        )
        lActions['move'] = url_for(
            'fsMoveFileView',
            quotedFilePath=urllib.parse.quote_plus('/'.join(linkPath)),
        )
    #
    if prepareParentButton:
        lActions['parent'] = url_for(
            'lsView',
            lsPathString='/'.join(linkPath[:-1]),
        )
    #
    return {
        k: v
        for k, v in lActions.items()
        if k not in discardedActions
    }


def prepareLinkInfo(db, link):
    """Calculate link information for display."""
    return [
        infoItem
        for infoItem in (
            {
                'action': 'Created',
                'actor': getUserFullName(db, link.creator_username),
            },
            {
                'action': 'Icon',
                'actor': getUserFullName(db, link.icon_file_id_username),
            },
            {
                'action': 'Metadata',
                'actor': getUserFullName(db, link.metadata_username),
            },
        )
        if infoItem['actor'] is not None
    ]


def prepareFileActions(db, file, filePath, parentBox, user,
                       discardedActions=set(), prepareParentButton=False):
    """ Calculate the actions on a file available to user (according to their
        powers) for showing in the file-as-ls-item view.
    """
    fActions = {}
    # view
    if isFileViewable(file):
        fActions['view'] = url_for('fsView', fsPathString='/'.join(filePath))
    # download
    fActions['download'] = url_for(
        'fsDownloadView',
        fsPathString='/'.join(filePath),
    )
    # active stuff
    if userHasPermission(db, user, parentBox. permissions, 'w'):
        if isFileTextEditable(file):
            fActions['text_edit'] = url_for(
                'editTextFileView',
                fsPathString='/'.join(filePath),
            )
        fActions['icon'] = url_for(
            'setIconView',
            mode='f',
            itemPathString='/'.join(filePath),
        )
        fActions['metadata'] = url_for(
            'fsMetadataView',
            fsPathString='/'.join(filePath),
        )
        fActions['delete'] = url_for(
            'fsDeleteFileView',
            fsPathString='/'.join(filePath),
        )
        fActions['move'] = url_for(
            'fsMoveFileView',
            quotedFilePath=urllib.parse.quote_plus('/'.join(filePath)),
        )
    # ticketing of files
    if user.is_authenticated:
        if userIsAdmin(db, user) or userHasRole(db, user, 'ticketer'):
            fActions['ticket'] = url_for(
                'fsMakeTicketView',
                fsPathString='/'.join(filePath),
            )
    #
    if prepareParentButton:
        fActions['parent'] = url_for(
            'lsView',
            lsPathString='/'.join(filePath[:-1]),
        )
    #
    return {
        k: v
        for k, v in fActions.items()
        if k not in discardedActions
    }


def prepareRootTasks(db, g, user):
    """ Combine all custom-page tree (and apply logic such as 'is user admin?')
        to calculate the whole (array of) special tasks available for showing
        as 'tasks' in the ls view of root box.
    """
    appShortName = g.settings['behaviour']['behaviour_appearance'][
        'application_short_name']['value']
    fixedPart = [
        extractTopLevelTaskFromTreeDescriptor(
            toolsPageDescriptor,
            'tool_task',
            g,
        ),
        extractTopLevelTaskFromTreeDescriptor(
            infoPageDescriptor,
            'info_task',
            g,
        ),
    ]
    if user.is_authenticated:
        userPart = [
            extractTopLevelTaskFromTreeDescriptor(
                userProfilePageDescriptor,
                'user_task',
                g,
                overrides={
                    'description': userProfileTitler(db, user),
                    'thumbnail': userProfileThumbnailer(db, user),
                },
            ),
        ]
        logoutPart = [
            {
                'name': logoutTitle(g),
                'description': logoutSubtitle(g),
                'url': url_for('logoutView'),
                'bgcolor': g.settings['color']['task_colors'][
                    'user_task']['value'],
                'thumbnail': makeSettingImageUrl(g, 'user_images', 'logout'),
            },
        ]
        if userIsAdmin(db, user):
            adminPart = [
                extractTopLevelTaskFromTreeDescriptor(
                    adminPageDescriptor,
                    'admin_task',
                    g,
                ),
            ]
        else:
            adminPart = []
    else:
        userPart = [
            {
                'name': loginTitle(g),
                'description': loginSubtitle(g),
                'url': url_for('loginView'),
                'bgcolor': g.settings['color']['task_colors'][
                    'user_task']['value'],
                'thumbnail': makeSettingImageUrl(g, 'user_images', 'login'),
            },
        ]
        logoutPart = []
        adminPart = []
    #
    return userPart + adminPart + fixedPart + logoutPart
