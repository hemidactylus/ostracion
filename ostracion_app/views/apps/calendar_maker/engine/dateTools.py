"""
    dateTools.py
"""

import datetime

from ostracion_app.utilities.tools.dictTools import (
    convertIterableToDictOfLists,
)


def getDaysOfMonth(startingDate):
    """
        Given a starting date, list all forward dates belonging to that month.
    """
    thisDate = startingDate
    month = thisDate.month
    dates = []
    while thisDate.month == month:
        dates.append(
            {
                'date': thisDate,
                'weekday': thisDate.weekday(),
            }
        )
        thisDate += datetime.timedelta(days=1)
    return dates


def regroupDaysOfMonth(dateList, rowStartingWeekday):
    """
        Regroup a list of dates into 'groups', that would be the rows
        of a calendar.
        Groups are in a dictionary, with their index as key.
        Each group is a dictionary weekday -> date (not necessarily full).
    """
    lineChangeIndices = [
        dInd
        for dInd, d in list(enumerate(dateList))[1:]
        if d['weekday'] == rowStartingWeekday
    ]
    #
    enrichedDates = [
        {
            'dateStruct': d,
            'row': sum(
                1 if lcInd <= dInd
                else 0
                for lcInd in lineChangeIndices
            ),
        }
        for dInd, d in enumerate(dateList)
    ]
    #
    groups = convertIterableToDictOfLists(
        enrichedDates,
        keyer=lambda ed: ed['row'],
        valuer=lambda ed: ed['dateStruct'],
    )
    regrouped = {
        gInd: {
            gD['weekday']: gD['date']
            for gD in gDays
        }
        for gInd, gDays in groups.items()
    }
    return regrouped


def makeWeekdayIndexSequence(rowStartingWeekday):
    """
        Prepare the list of weekday indices
        dictating ordering in each calendar row.
    """
    return [
        (rowStartingWeekday + i) % 7
        for i in range(7)
    ]


def countMonths(iniY, iniM, endY, endM):
    """Calculate the number of months (calendar pages) of a calendar."""
    if any(v is None for v in [iniY, iniM, endY, endM]):
        return None
    else:
        if (iniY, iniM) > (endY, endM):
            return None
        else:
            return len(list(makeListOfMonths(iniY, iniM, endY, endM)))


def makeListOfMonths(iniY, iniM, endY, endM):
    """Prepare a list of all months (dates) for a calendar."""
    _y, _m = iniY, iniM
    while (_y, _m) <= (endY, endM):
        yield datetime.date(_y, _m, 1)
        if _m == 12:
            _y += 1
        _m = 1 + _m % 12
