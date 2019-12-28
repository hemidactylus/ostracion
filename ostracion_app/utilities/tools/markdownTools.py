""" markdownTools.py
    Low-level and specific applications of the md -> dom preparations.
"""

import os
import markdown

from flask import (
    url_for,
)

from ostracion_app.utilities.fileIO.thumbnails import (
    createTransparentTextImage,
    determineManagedTextImagePath,
)

from config import (
    ostracionVersion,
)

from ostracion_app.utilities.tools.formatting import (
    applyReplacementPairs,
)


def loadMarkdownReplacements(settings):
    """ Return the list of markdown special '[[NAME]]' macros
        (or 'replacements').
        These are defined by hand here.
    """
    dummyDPOEmailId = determineManagedTextImagePath(
        settings['privacy_policy']['privacy_policy']['dpo_email']['value'],
        prefix='privacy_policy/dpo_email',
    )[2],
    dummyContactInfoId = determineManagedTextImagePath(
        settings['about']['about']['about_contact_info']['value'],
        prefix='about/about_contact_info',
    )[2],
    applicationLongName = settings['behaviour']['behaviour_appearance'][
        'application_long_name']['value']
    applicationShortName = settings['behaviour']['behaviour_appearance'][
        'application_short_name']['value']
    #
    replacements = [
        (
            '[[DPO_EMAIL_PICTURE]]',
            '<img src="%s" style="height:1rem;"/>' % (
                url_for('DPOEmailImageView', dummyId='%s_' % dummyDPOEmailId),
            ),
        ),
        (
            '[[CONTACT_INFO_PICTURE]]',
            '<img src="%s" style="height:1rem;"/>' % (
                url_for(
                    'contactInfoImageView',
                    dummyId='%s_' % dummyContactInfoId,
                ),
            ),
        ),
        (
            '[[APPLICATION_NAME]]',
            applicationLongName,
        ),
        (
            '[[APPLICATION_SHORT_NAME]]',
            applicationShortName,
        ),
        (
            '[[OSTRACION_VERSION]]',
            ostracionVersion,
        ),
    ]
    #
    return replacements


def markdownToHtml(markdownBody, replacements):
    """ Make a markdown text into a full-fledged DOM."""
    return markdown.markdown(
        applyReplacementPairs(
            markdownBody,
            replacements,
        ),
        extensions=['markdown.extensions.tables'],
    )
