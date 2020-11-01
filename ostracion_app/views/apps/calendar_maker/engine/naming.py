"""
    naming.py
"""

from ostracion_app.views.apps.calendar_maker.engine.settings import (
    weekdayNamesPerLanguage,
    monthNamesPerLanguage,
)


def getMonthName(mIndex, language):
    return monthNamesPerLanguage[language][mIndex - 1]


def getWeekdayName(wdIndex, language):
    return weekdayNamesPerLanguage[language][wdIndex]


def printMonth(stDate, groups, language, wdIndexSequence):
    print('\n    %s' % ('==='*7))
    print(
        '    ** Date: %s, %s **' % (
            getMonthName(stDate.month, language),
            stDate.year,
        )
    )
    print('    %s' % ('---'*7))
    print('    %s' % (' '.join(
        weekdayNamesPerLanguage[language][i]
        for i in wdIndexSequence
    )))
    for g, gConts in sorted(groups.items()):
        dateDescs = [
            '  ' if i not in gConts else '%2i' % gConts[i].day
            for i in wdIndexSequence
        ]
        print('    %s' % (' '.join(dateDescs)))
