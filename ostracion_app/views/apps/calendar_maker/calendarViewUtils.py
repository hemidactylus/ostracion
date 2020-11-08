"""
    calendarViewUtils.py
"""

import json
from flask import (
    redirect,
    url_for,
)

from ostracion_app.utilities.tools.dictTools import (
    recursivelyMergeDictionaries
)

from ostracion_app.views.apps.calendar_maker.engine.calendarTools import (
    defaultCalendarProperties,
)


def cookiesToCurrentCalendar(cookies):
    """
        Extract, from the passed request 'cookies',
        all currently stored settings for the calendar generation.
    """
    cpCookie = cookies.get('apps_calendarmaker_current')
    if cpCookie is None:
        calFromCookie = {}
    else:
        calFromCookie = json.loads(cpCookie)
    # defaults
    defaultCal = {
        'properties': defaultCalendarProperties()
    }
    #
    return recursivelyMergeDictionaries(
        calFromCookie,
        defaultMap=defaultCal,
    )


def dressResponseWithCurrentCalendar(response, calendarToSet):
    """
        Dress a response from a view function by making it also
        set the cookie with the calendar information.
    """
    response.set_cookie(
        'apps_calendarmaker_current',
        json.dumps(calendarToSet),
    )
    return response


def applyReindexingToImages(req, idxMap):
    """
        Apply an altered index-to-new-position map
        to the selected calendar images and build the response
        which cookifies the choice.
        Abstracts deletion and swaps among chosen calendar images.
    """
    response = redirect(url_for('calendarMakerImagesView'))
    currentCalendar = cookiesToCurrentCalendar(req.cookies)
    prevImages = currentCalendar.get('image_path_strings', [])
    images = [
        prevImages[idxMap.get(idx, idx)]
        for idx in range(len(prevImages))
        if idxMap.get(idx, idx) is not None
        if idxMap.get(idx, idx) >= 0
        if idxMap.get(idx, idx) < len(prevImages)
    ]
    dResponse = dressResponseWithCurrentCalendar(
        response,
        recursivelyMergeDictionaries(
            {'image_path_strings': images},
            defaultMap=currentCalendar
        ),
    )
    return dResponse
