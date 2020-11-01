"""
    calendarEngine.py
"""


from jinja2 import Environment, PackageLoader, select_autoescape

from ostracion_app.views.apps.calendar_maker.engine.dateTools import (
    makeListOfMonths,
    getDaysOfMonth,
    regroupDaysOfMonth,
    makeWeekdayIndexSequence,
)

from ostracion_app.views.apps.calendar_maker.engine.naming import (
    getMonthName,
    getWeekdayName,
    printMonth,
)


env = Environment(
    loader=PackageLoader('ostracion_app.views.apps.calendar_maker', 'templates'),
)


def makeCalendarTexfile(calStructure, outFileName):
    calTemplate = env.get_template('calendar.tex.j2')
    open(outFileName, 'w').write(
        calTemplate.render(
            pages=calStructure['pages'],
            wdIndexSequence=calStructure['weekdayIndexSequence'],
            weekdayNames=calStructure['weekdayNames'],
            coverImage=calStructure['coverImagePath'],
        )
    )


def makeCalendarPage(sDate, language, startingWeekday):
    days = getDaysOfMonth(sDate)
    groups = regroupDaysOfMonth(days, startingWeekday)
    printMonth(
        sDate,
        groups,
        language=language,
        wdIndexSequence=makeWeekdayIndexSequence(rowStartingWeekday=startingWeekday),
    )
    return {
        'monthName': getMonthName(sDate.month, language=language),
        'yearName': sDate.year,
        'groups': groups,
        'image': 'TODO_%s' % sDate,
    }


def makeCalendarPages(year0, month0, year1, month1, language, startingWeekday):
    return [
        makeCalendarPage(startingDate, language, startingWeekday)
        for startingDate in makeListOfMonths(
            year0,
            month0,
            year1,
            month1,
        )
    ]


def makeCalendarWeekdayNameMap(language):
    return {
        i: getWeekdayName(i, language)
        for i in range(7)
    }


def makeCalendarStructure(properties):
    weekdayIndexSequence = makeWeekdayIndexSequence(rowStartingWeekday=properties['startingweekday'])
    weekdayNames = makeCalendarWeekdayNameMap(language=properties['language'])
    coverImagePath = 'TODO_COVER'
    pages = makeCalendarPages(
        properties['year0'],
        properties['month0'],
        properties['year1'],
        properties['month1'],
        language=properties['language'],
        startingWeekday=properties['startingweekday'],
    )
    return {
        'weekdayIndexSequence': weekdayIndexSequence,
        'weekdayNames': weekdayNames,
        'coverImagePath': coverImagePath,
        'pages': pages,
    }


if __name__ == '__main__':
    qProperties = {
        'month0': 10,
        'year0': 2020,
        'month1': 12,
        'year1': 2020,
        'language': 'it',
        'startingweekday': 0,
    }
    #
    calendarStructure = makeCalendarStructure(qProperties)
    #
    makeCalendarTexfile(
        calendarStructure,
        '/home/stefano/temp/NotBackedUp/Tests/symlinks_for_latex_calendar/fromOstra/A.tex',
    )
