""" find.py
    Views related to the search facilities.
"""

import time

from ostracion_app.app_main import app

from flask import (
    redirect,
    url_for,
    render_template,
    g,
    send_from_directory,
    abort,
    request,
)

from ostracion_app.utilities.viewTools.messageTools import flashMessage

from ostracion_app.utilities.forms.forms import (
    FindForm,
    QuickFindForm,
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)

from ostracion_app.utilities.database.findTools import (
    fsFind,
)

from ostracion_app.utilities.tools.formatting import (
    applyDefault,
)

from ostracion_app.utilities.database.settingsTools import (
    makeSettingImageUrl,
)

from ostracion_app.utilities.viewTools.pathTools import (
    prepareTaskPageFeatures,
)

from ostracion_app.views.viewTools.toolsPageTreeDescriptor import (
    toolsPageDescriptor,
)


@app.route('/find', methods=['GET', 'POST'])
def findView():
    """Complete (i.e. in-page) box- and file-find route."""
    user = g.user
    db = dbGetDatabase()
    form = FindForm()
    #
    if not g.canPerformSearch:
        raise OstracionError('Insufficient permissions')
    #
    if form.validate_on_submit():
        # search parameter collection
        searchMode = form.searchMode.data
        searchBoxes = form.searchTypeBoxes.data
        searchFiles = form.searchTypeFiles.data
        searchInDescription = form.searchFieldDescription.data
        searchTerm = form.text.data
        options = {
            'mode': searchMode,
            'searchBoxes': searchBoxes,
            'searchFiles': searchFiles,
            'useDescription': searchInDescription,
        }
        #
        initTime = time.time()
        findResults = fsFind(
            db,
            searchTerm,
            user,
            options=options,
        )
        elapsed = time.time() - initTime
        #
        pageFeatures = prepareTaskPageFeatures(
            toolsPageDescriptor,
            ['root', 'search'],
            g,
            overrides={
                'pageTitle': 'Search results',
                'pageSubtitle': 'Search term: "%s"' % searchTerm,
            },
        )
        return render_template(
            'findform.html',
            user=user,
            form=form,
            findResults=findResults,
            elapsed=elapsed,
            searchTerm=searchTerm,
            **pageFeatures,
        )
    else:
        #
        form.searchMode.data = applyDefault(
            form.searchMode.data,
            'sim_ci',
            additionalNulls=['None'],
        )
        noTargets = not(form.searchTypeBoxes.data or form.searchTypeFiles.data)
        if noTargets:
            form.searchTypeBoxes.data = True
            form.searchTypeFiles.data = True
        #
        pageFeatures = prepareTaskPageFeatures(
            toolsPageDescriptor,
            ['root', 'search'],
            g,
        )
        return render_template(
            'findform.html',
            user=user,
            form=form,
            results=None,
            **pageFeatures,
        )


@app.route('/quickfind', methods=['POST'])
def quickFindView():
    """Quick (i.e. in-navbar) box- and file-find route."""
    user = g.user
    db = dbGetDatabase()
    form = QuickFindForm()
    #
    if not g.canPerformSearch:
        raise OstracionError('Insufficient permissions')
    # search parameter collection
    searchMode = 'sim_ci'
    searchBoxes = True
    searchFiles = True
    searchInDescription = False
    searchTerm = form.quicktext.data if form.quicktext.data is not None else ''
    options = {
        'mode': searchMode,
        'searchBoxes': searchBoxes,
        'searchFiles': searchFiles,
        'useDescription': searchInDescription,
    }
    # recasting of the above default for the displayed form
    findForm = FindForm()
    findForm.searchMode.data = searchMode
    findForm.searchTypeBoxes.data = searchBoxes
    findForm.searchTypeFiles.data = searchFiles
    findForm.searchFieldDescription.data = searchInDescription
    findForm.text.data = searchTerm
    #
    initTime = time.time()
    findResults = fsFind(
        db,
        searchTerm,
        user,
        options=options,
    )
    elapsed = time.time() - initTime
    #
    return render_template(
        'findform.html',
        user=user,
        form=findForm,
        pageTitle='Search Results',
        pageSubtitle='Search term: "%s"' % searchTerm,
        iconUrl=makeSettingImageUrl(g, 'app_images', 'search'),
        breadCrumbs=[
            {
                'name': 'Tools',
                'type': 'link',
                'target': None,
                'link': False,
            },
            {
                'name': 'Search',
                'type': 'link',
                'target': None,
                'link': False,
            },
        ],
        findResults=findResults,
        elapsed=elapsed,
        searchTerm=searchTerm,
    )
