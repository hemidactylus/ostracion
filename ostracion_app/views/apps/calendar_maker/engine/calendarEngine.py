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
    maxCalendarImageResolutionWidth,
)

from ostracion_app.utilities.fileIO.physical import (
    makeSymlink,
)

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
)

env = Environment(
    loader=PackageLoader(
        'ostracion_app.views.apps.calendar_maker',
        'templates',
    ),
)


def duplicateImageForCalendar(src, dst):
    """
        Given a source file (e.g. a standard Ostracion physical filepath)
        and a destination filepath to create (with extension, amenable to
        LaTeX), generate the latter and return its path.
        May be a simple symlink or a new, capped-res file, to optimize
        calendar pdf for file size.
    """
    args = [
        'convert',
        src,
        '-resize',
        '%ix>' % maxCalendarImageResolutionWidth,
        dst,
    ]
    imgDuplicationOutput = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if imgDuplicationOutput.returncode == 0:
        if os.path.isfile(dst):
            return dst
        else:
            raise OstracionError('Could not resize input image')
            return None
    else:
        raise OstracionError('Could not resize input image')
        return None


def makeCalendarTexfile(calStructure, outFileName):
    """
        Given a full calendar description 'calStructure',
        generate a ready-to-compile TeX-file with desired filename.
    """
    calTemplate = env.get_template('calendar.tex.j2')
    open(outFileName, 'w').write(
        calTemplate.render(
            **calStructure
        )
    )


def makeCalendarPage(sDate, iTexPath, language, startingWeekday):
    """Generate the structure describing a calenda 'page' (i.e. month)."""
    days = getDaysOfMonth(sDate)
    groups = regroupDaysOfMonth(days, startingWeekday)
    # printMonth(
    #     sDate,
    #     groups,
    #     language=language,
    #     wdIndexSequence=makeWeekdayIndexSequence(
    #         rowStartingWeekday=startingWeekday,
    #     ),
    # )
    return {
        'monthName': getMonthName(sDate.month, language=language),
        'yearName': sDate.year,
        'groups': groups,
        'imageTexPath': iTexPath,
    }


def makeCalendarPages(year0, month0, year1, month1, imageTexPaths,
                      language, startingWeekday):
    """Generate a list of calendar-structure 'page' objects, for all months."""
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
    """Prepare a list weekday index -> weekday name"""
    return {
        i: getWeekdayName(i, language)
        for i in range(7)
    }


def makeCalendarStructure(properties, imageTexPaths, coverImageTexPath):
    """
        Prepare the full structure of a calendar, ready to be given the
        template generation function.
    """
    weekdayIndexSequence = makeWeekdayIndexSequence(
        rowStartingWeekday=properties['startingweekday'],
    )
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
        Generate the pdf of a calendar given its properties.
        Uses 'pdflatex' under the hood.

        Input
            properties:         a dictionary with all required properties
            imageTexPaths:      an array of physical-files-to-use
            coverImageTexPath:  a single path to the cover physical-image-file
            workingDirectory:   where to generate all files (incl. final pdf)
            pdfTitle:           pdf-name, without extension

        Output
            pdfTitleOrNone, [tempFileToDelete_1, ...]

        pdfTitleOrNone is None upon failures.
        It is care of the caller to arrange deletion of temporary files.
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
