"""
    calendarTools.py
"""

import datetime

from ostracion_app.views.apps.calendar_maker.engine.settings import (
    languageMap,
    startingWeekdayMap,
)


def describeSettings(calProperties):
    """Make the calendar properties into a string summarizing them."""
    languageName = languageMap.get(calProperties.get('language'))
    startingweekdayName = startingWeekdayMap.get(
        str(calProperties.get('startingweekday'))
    )
    year0 = calProperties.get('year0')
    month0 = calProperties.get('month0')
    year1 = calProperties.get('year1')
    month1 = calProperties.get('month1')
    #
    usefulValues = (
        languageName,
        startingweekdayName,
        year0,
        month0,
        year1,
        month1,
    )
    #
    if all([q is not None for q in usefulValues]):
        datesDesc = 'Time: %i/%i to %i/%i' % (
            month0,
            year0,
            month1,
            year1,
        )
        languageDesc = 'Language: %s' % languageName
        swDesc = 'Rows start with: %s' % startingweekdayName
        description = [
            datesDesc,
            languageDesc,
            swDesc,
        ]
        return description
    else:
        return None


def defaultCalendarProperties():
    """Generate the default properties of a calendar."""
    currentYear = datetime.datetime.now().year
    return {
        'month0': 1,
        'year0': currentYear + 1,
        'month1': 12,
        'year1': currentYear + 1,
        'language': 'en',
        'startingweekday': 6,
    }
