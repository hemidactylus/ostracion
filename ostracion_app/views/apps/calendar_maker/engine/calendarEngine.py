"""
    calendarEngine.py
"""

import os
import subprocess
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

from ostracion_app.views.apps.calendar_maker.engine.settings import (
    pdfGenerationTimeoutSeconds,
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

env = Environment(
    loader=PackageLoader('ostracion_app.views.apps.calendar_maker', 'templates'),
)


def makeCalendarTexfile(calStructure, outFileName):
    """
        TO DOC
        eats structure with everything (incl. final paths for images)
        and creates texfile
    """
    calTemplate = env.get_template('calendar.tex.j2')
    open(outFileName, 'w').write(
        calTemplate.render(
            **calStructure
        )
    )


def makeCalendarPage(sDate, iTexPath, language, startingWeekday):
    days = getDaysOfMonth(sDate)
    groups = regroupDaysOfMonth(days, startingWeekday)
    # printMonth(
    #     sDate,
    #     groups,
    #     language=language,
    #     wdIndexSequence=makeWeekdayIndexSequence(rowStartingWeekday=startingWeekday),
    # )
    return {
        'monthName': getMonthName(sDate.month, language=language),
        'yearName': sDate.year,
        'groups': groups,
        'imageTexPath': iTexPath,
    }


def makeCalendarPages(year0, month0, year1, month1, imageTexPaths, language, startingWeekday):
    return [
        makeCalendarPage(startingDate, imagePath, language, startingWeekday)
        for imagePath, startingDate in zip(
            imageTexPaths,
            makeListOfMonths(
                year0,
                month0,
                year1,
                month1,
            ),
        )
    ]


def makeCalendarWeekdayNameMap(language):
    return {
        i: getWeekdayName(i, language)
        for i in range(7)
    }


def makeCalendarStructure(properties, imageTexPaths, coverImageTexPath):
    weekdayIndexSequence = makeWeekdayIndexSequence(rowStartingWeekday=properties['startingweekday'])
    weekdayNames = makeCalendarWeekdayNameMap(language=properties['language'])
    pages = makeCalendarPages(
        properties['year0'],
        properties['month0'],
        properties['year1'],
        properties['month1'],
        imageTexPaths=imageTexPaths,
        language=properties['language'],
        startingWeekday=properties['startingweekday'],
    )
    return {
        'weekdayIndexSequence': weekdayIndexSequence,
        'weekdayNames': weekdayNames,
        'coverImageTexPath': coverImageTexPath,
        'pages': pages,
    }


def makeCalendarPdf(properties, imageTexPaths, coverImageTexPath,
                    workingDirectory, pdfTitle):
    """
        TO DOC

        Input: properties+workdir+fileTitle+texpaths
        Output: a created pdf-path or None, an array of temp file paths
            (for later destruction), which does NOT include the pdf itself

        RUNNING:
            pdflatex  A.tex
            (but in the right directory!)
    """
    # generating
    calendarStructure = makeCalendarStructure(properties, imageTexPaths,
                                              coverImageTexPath)
    outputTexFile = '%s.tex' % pdfTitle
    outputPdfFile = '%s.pdf' % pdfTitle
    outputTexPath = os.path.join(workingDirectory, outputTexFile)
    outputPdfPath = os.path.join(workingDirectory, outputPdfFile)
    makeCalendarTexfile(calendarStructure, outputTexPath)
    # compiling, checking+returning the resulting file
    pdfMakingOutput = subprocess.run(
        [
            'timeout',
            '%is' % pdfGenerationTimeoutSeconds,
            'pdflatex',
            '-halt-on-error',
            outputTexFile,
        ],
        cwd=workingDirectory,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if pdfMakingOutput.returncode == 0:
        if os.path.isfile(outputPdfPath):
            finalPdfPath = outputPdfPath
        else:
            raise OstracionError('Could not retrieve generated calendar')
            finalPdfPath = None
    else:
        raise OstracionError('Calendar generation command failed')
        finalPdfPath = None
    temporaryFiles = [
        os.path.join(workingDirectory, '%s.%s' % (pdfTitle, extension))
        for extension in ['tex', 'log', 'aux']
    ]    
    return finalPdfPath, temporaryFiles
