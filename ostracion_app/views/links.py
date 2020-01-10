""" links.py
    Views related to operating with links
"""

from datetime import datetime
import urllib.parse

from werkzeug.utils import secure_filename

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

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)

from ostracion_app.utilities.models.Link import Link

from ostracion_app.utilities.tools.formatting import (
    applyDefault,
)

from ostracion_app.utilities.fileIO.physical import (
    flushFsDeleteQueue,
)

from ostracion_app.utilities.database.fileSystem import (
    getBoxFromPath,
    makeLinkInParent,
    getLinkFromParent,
    deleteLink,
    updateLink,
    getRootBox,
    moveLink,
)

from ostracion_app.utilities.tools.treeTools import (
    getMaxTreeDepth,
    collectTreeFromBox,
    treeAny,
)

from ostracion_app.utilities.viewTools.pathTools import (
    makeBreadCrumbs,
    splitPathString,
)

from ostracion_app.utilities.forms.forms import (
    EditLinkForm,
)

from ostracion_app.utilities.database.settingsTools import (
    makeSettingImageUrl,
)

from ostracion_app.utilities.tools.colorTools import (
    prepareColorShadeMap,
)

from ostracion_app.utilities.database.permissions import (
    userHasPermission,
)


@app.route('/mklink', methods=['GET', 'POST'])
@app.route('/mklink/', methods=['GET', 'POST'])
@app.route('/mklink/<path:fsPathString>', methods=['GET', 'POST'])
def makeLinkView(fsPathString=''):
    """Generate-new-link route."""
    user = g.user
    form = EditLinkForm()
    db = dbGetDatabase()
    boxPath = splitPathString(fsPathString)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    parentBoxPath = boxPath
    parentBox = getBoxFromPath(db, parentBoxPath, user)
    if form.validate_on_submit():
        linkName = secure_filename(form.linkname.data)
        linkDescription = form.linkdescription.data
        linkTarget = form.linktarget.data
        openInNewWindow = form.openinnewwindow.data
        savingResult = makeLinkInParent(
            db=db,
            user=user,
            parentBox=parentBox,
            date=datetime.now(),
            linkName=linkName,
            linkDescription=linkDescription,
            linkTarget=linkTarget,
            linkOptions={
                'open_in_new_window': openInNewWindow,
            },
        )
        return redirect(url_for(
            'lsView',
            lsPathString=fsPathString,
        ))
    else:
        pathBCrumbs = makeBreadCrumbs(
            parentBoxPath,
            g,
            appendedItems=[{
                'kind': 'link',
                'target': None,
                'name': 'New link',
            }],
        )
        form.openinnewwindow.data = True
        return render_template(
            'makelink.html',
            form=form,
            user=user,
            breadCrumbs=pathBCrumbs,
            iconUrl=makeSettingImageUrl(g, 'app_images', 'external_link'),
            pageTitle='New link',
            pageSubtitle='Create a new link in "%s"' % (
                parentBox.box_name if parentBox.box_id != '' else '(root)'
            ),
        )


@app.route('/fslinkrm/<path:fsPathString>')
@app.route('/fslinkrm/')
@app.route('/fslinkrm')
def fsDeleteLinkView(fsPathString=''):
    """ Delete-link view.
        Permission checks are performed by the deleteLink filesystem call.
    """
    user = g.user
    db = dbGetDatabase()
    fileStorageDirectory = g.settings['system']['system_directories'][
        'fs_directory']['value']
    lsPath = splitPathString(fsPathString)
    boxPath, linkName = lsPath[:-1], lsPath[-1]
    parentBox = getBoxFromPath(db, boxPath, user)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    link = getLinkFromParent(db, parentBox, linkName, user)
    fsDeleteQueue = deleteLink(
        db,
        parentBox,
        link,
        user,
        fileStorageDirectory=fileStorageDirectory,
    )
    flushFsDeleteQueue(fsDeleteQueue)
    return redirect(url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    ))


@app.route('/mdlink', methods=['GET', 'POST'])
@app.route('/mdlink/', methods=['GET', 'POST'])
@app.route('/mdlink/<path:fsPathString>', methods=['GET', 'POST'])
def fsLinkMetadataView(fsPathString=''):
    """Edit-link-metadata view, a web-form."""

    user = g.user
    db = dbGetDatabase()
    form = EditLinkForm()
    lsPath = splitPathString(fsPathString)
    boxPath, prevLinkName = lsPath[:-1], lsPath[-1]
    parentBox = getBoxFromPath(db, boxPath, user)
    request._onErrorUrl = url_for(
        'lsView',
        lsPathString='/'.join(boxPath[1:]),
    )
    link = getLinkFromParent(db, parentBox, prevLinkName, user)
    if form.validate_on_submit():
        newLink = Link(
            **recursivelyMergeDictionaries(
                {
                    'name': form.linkname.data,
                    'description': form.linkdescription.data,
                    'target': form.linktarget.data,
                    'metadata_username': (user.username
                                          if user.is_authenticated
                                          else ''),
                    'metadata_dict': {
                        'open_in_new_window': form.openinnewwindow.data,
                    },
                },
                defaultMap={
                    k: v
                    for k, v in link.asDict().items()
                    if k not in {'metadata'}
                },
            )
        )
        updateLink(db, boxPath, prevLinkName, newLink, user)
        return redirect(url_for('lsView', lsPathString='/'.join(boxPath[1:])))
    else:
        form.linkname.data = applyDefault(
            form.linkname.data,
            link.name
        )
        form.linkdescription.data = applyDefault(
            form.linkdescription.data,
            link.description
        )
        form.linktarget.data = applyDefault(
            form.linktarget.data,
            link.target
        )
        form.openinnewwindow.data = link.getMetadata(
            'open_in_new_window',
            True,
        )
        #
        pageFeatures = {
            'breadCrumbs': makeBreadCrumbs(
                boxPath,
                g,
                appendedItems=[
                    {
                        'kind': 'external_link',
                        'target': link,
                    },
                    {
                        'kind': 'link',
                        'target': None,
                        'name': 'Metadata',
                    }
                ],
            ),
            'pageTitle': 'Edit link metadata (%s)' % link.name,
            'pageSubtitle': 'Name and target are mandatory',
            'iconUrl': url_for(
                'linkThumbnailView',
                dummyId=link.icon_file_id + '_',
                fsPathString='/'.join(lsPath[1:]),
            ),
        }
        return render_template(
            'makelink.html',
            form=form,
            user=user,
            **pageFeatures,
        )


@app.route('/mvlink/<quotedLinkPath>')
def fsMoveLinkView(quotedLinkPath):
    """Move-link, view 1/2: select destination box."""
    user = g.user
    db = dbGetDatabase()
    # first we find the link
    fsPathString = urllib.parse.unquote_plus(quotedLinkPath)
    lsPath = splitPathString(fsPathString)
    boxPath, linkName = lsPath[:-1], lsPath[-1]
    parentBox = getBoxFromPath(db, boxPath, user)
    link = getLinkFromParent(db, parentBox, linkName, user)
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
        g.settings['color']['navigation_colors']['link']['value'],
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
        mode='link_move',
        object_quoted_path=quotedLinkPath,
        colorShadeMap=colorShadeMap,
        user=user,
        iconUrl=makeSettingImageUrl(g, 'app_images', 'move'),
        pageTitle='Select link destination',
        pageSubtitle=(('Choose the box to which link "%s" shall '
                       'be moved from "%s"') % (
                        link.name,
                        '/'.join(boxPath) if len(boxPath) > 1 else "Root",
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
                    'kind': 'external_link',
                    'target': link,
                },
                {
                    'kind': 'link',
                    'target': None,
                    'name': 'Move link',
                }
            ],
        ),
    )


@app.route('/domvlink/<quotedLinkPath>/<quotedDestBox>')
@app.route('/domvlink/<quotedLinkPath>/')
@app.route('/domvlink/<quotedLinkPath>')
def fsDoMoveLinkView(quotedLinkPath, quotedDestBox=''):
    """Move-link, view 2/2: dest box is selected, actually move."""
    user = g.user
    db = dbGetDatabase()
    # we retrieve the source file and the destination box
    srcFsPathString = urllib.parse.unquote_plus(quotedLinkPath)
    srcLsPath = splitPathString(srcFsPathString)
    srcBoxPath, linkName = srcLsPath[:-1], srcLsPath[-1]
    srcBox = getBoxFromPath(db, srcBoxPath, user)
    link = getLinkFromParent(db, srcBox, linkName, user)
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
    messages = moveLink(
        db,
        link,
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
