"""
    utilities.py
"""

import urllib.parse

from flask import (
    redirect,
    url_for,
    render_template,
    request,
    g,
)

from ostracion_app.utilities.database.settingsTools import (
    makeSettingImageUrl,
)

from ostracion_app.utilities.tools.treeTools import (
    getMaxTreeDepth,
    collectTreeFromBox,
)

from ostracion_app.utilities.tools.colorTools import (
    prepareColorShadeMap,
)


def preparePickBoxPage(db, user, callbackUrl, startBox, message, predicate=lambda richFileOrBox: True):
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
