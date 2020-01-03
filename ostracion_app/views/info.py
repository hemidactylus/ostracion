""" info.py
    views for information/about/policy/guides...
"""

import json
import os
import datetime

from ostracion_app.app_main import app

from flask import (
    render_template,
    g,
    send_from_directory,
    abort,
    Response,
)

from config import (
    ostracionVersion,
)

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)

from ostracion_app.utilities.database.settingsTools import (
    makeSettingImageUrl,
)

from ostracion_app.utilities.tools.markdownTools import (
    markdownToHtml,
    loadMarkdownReplacements,
)

from config import (
    resourceDirectory,
)

from ostracion_app.utilities.database.permissions import (
    userRoleRequired,
    userIsAdmin,
)

from ostracion_app.utilities.viewTools.pathTools import (
    prepareTaskPageFeatures,
)

from ostracion_app.utilities.viewTools.textImageTools import (
    prepareTextualImageForView,
)

from ostracion_app.views.viewTools.infoPageTreeDescriptor import (
    infoPageDescriptor,
)

from ostracion_app.views.viewTools.pageTreeDescriptorTools import (
    filterToolsPageDescriptor,
)


@app.route('/info')
def infoHomeView():
    """Main info page with tasks."""
    user = g.user
    db = dbGetDatabase()
    #
    filteredInfoPageDescriptor = filterToolsPageDescriptor(
        infoPageDescriptor,
        subTasksAccessibility={
            'root': {
                'admin_guide':  userIsAdmin(db, user),
            },
        },
    )
    #
    pageFeatures = prepareTaskPageFeatures(
        filteredInfoPageDescriptor,
        ['root'],
        g,
    )
    return render_template(
        'tasks.html',
        user=user,
        bgcolor=g.settings['color']['task_colors']['info_task']['value'],
        **pageFeatures,
    )


@app.route('/info/userguide')
def userGuideView():
    """Guide to app for users."""
    user = g.user
    db = dbGetDatabase()
    #
    userGuideContents = markdownToHtml(
        open(
            os.path.join(
                resourceDirectory,
                'guides_markdown',
                'user_guide.md',
            )
        ).read(),
        replacements=loadMarkdownReplacements(g.settings),
    )
    #
    pageFeatures = prepareTaskPageFeatures(
        infoPageDescriptor,
        ['root', 'user_guide'],
        g,
    )
    return render_template(
        'guide.html',
        user=user,
        contents=userGuideContents,
        **pageFeatures,
    )


@app.route('/info/adminguide')
@userRoleRequired({'admin'})
def adminGuideView():
    """Guide to app for admins."""
    user = g.user
    db = dbGetDatabase()
    adminGuideContents = markdownToHtml(
        open(
            os.path.join(
                resourceDirectory,
                'guides_markdown',
                'admin_guide.md',
            )
        ).read(),
        replacements=loadMarkdownReplacements(g.settings),
    )
    #
    pageFeatures = prepareTaskPageFeatures(
        infoPageDescriptor,
        ['root', 'admin_guide'],
        g,
    )
    return render_template(
        'guide.html',
        user=user,
        contents=adminGuideContents,
        **pageFeatures,
    )


@app.route('/info/privacy')
def privacyPolicyView():
    """Privacy policy route."""
    user = g.user
    db = dbGetDatabase()
    privacyPolicy = {
        'contents': markdownToHtml(
            g.settings['privacy_policy']['privacy_policy'][
                'privacy_policy_body']['value'],
            replacements=loadMarkdownReplacements(g.settings),
        ),
    }
    ppVersion = g.settings['privacy_policy']['privacy_policy'][
        'privacy_policy_version']['value']
    ppDate = g.settings['privacy_policy']['privacy_policy'][
        'privacy_policy_date']['value']
    #
    pageFeatures = prepareTaskPageFeatures(
        infoPageDescriptor,
        ['root', 'privacy'],
        g,
        overrides={
            'pageSubtitle': 'Version %s' % ppVersion if ppVersion else None,
            'pageSubtitleit': 'dated %s' % ppDate if ppDate else None,
        },
    )
    #
    return render_template(
        'privacypolicy.html',
        user=user,
        privacyPolicy=privacyPolicy,
        **pageFeatures,
    )


@app.route('/info/about')
def aboutView():
    """<About the app> route."""
    user = g.user
    db = dbGetDatabase()
    #
    aboutInstanceSpecificContents = markdownToHtml(
        g.settings['about']['about']['about_instance_body']['value'],
        replacements=loadMarkdownReplacements(g.settings),
    )
    aboutContents = markdownToHtml(
        g.settings['about']['about']['about_body']['value'],
        replacements=loadMarkdownReplacements(g.settings),
    )
    #
    appLongName = g.settings['behaviour']['behaviour_appearance'][
        'application_long_name']['value']
    pageFeatures = prepareTaskPageFeatures(
        infoPageDescriptor,
        ['root', 'about'],
        g,
        overrides={
            'pageTitle': 'About Ostracion / %s' % appLongName,
            'pageSubtitle': 'An online shared file system',
        },
    )
    #
    return render_template(
        'about.html',
        user=user,
        appSecondImageUrl=makeSettingImageUrl(
            g,
            'ostracion_images',
            'application_about_image_2',
        ),
        aboutInstanceSpecificContents=aboutInstanceSpecificContents,
        aboutContents=aboutContents,
        ostracionVersion=ostracionVersion,
        **pageFeatures,
    )


@app.route('/robots.txt')
def robotsTxtView():
    """Implementation of the robots.txt resource. Behave as per settings."""
    returnRobotsTxt = g.settings['behaviour']['search'][
        'serve_robots_txt']['value']
    if returnRobotsTxt:
        robotsTxtContents = g.settings['behaviour']['search'][
            'robots_txt_body']['value']
        return Response(robotsTxtContents, mimetype='text/plain')
    else:
        return abort(404)


@app.route('/info/<dummyId>/dpo_email.png')
def DPOEmailImageView(dummyId):
    """Serve the image containing the text of 'dpo email'."""
    return prepareTextualImageForView(
        dbGetDatabase(),
        g.user,
        imgText=g.settings['privacy_policy']['privacy_policy'][
            'dpo_email']['value'],
        imgPrefix='privacy_policy/dpo_email',
    )


@app.route('/info/<dummyId>/contact_info.png')
def contactInfoImageView(dummyId):
    """Serve the image containing the text of 'contact info'."""
    return prepareTextualImageForView(
        dbGetDatabase(),
        g.user,
        imgText=g.settings['about']['about'][
            'about_contact_info']['value'],
        imgPrefix='about/about_contact_info',
    )
