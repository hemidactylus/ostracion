""" links.py
    Views related to operating with links
"""

from datetime import datetime

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

from ostracion_app.utilities.database.fileSystem import (
    getBoxFromPath,
    saveLinkInParent,
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
        savingResult = saveLinkInParent(
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
