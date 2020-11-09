"""
    settings.py
"""

# these are properly Latex-escaped strings where needed
weekdayNamesPerLanguage = {
    'it': [
        'Luned\\\'i',
        'Marted\\\'i',
        'Mercoled\\\'i',
        'Gioved\\\'i',
        'Venerd\\\'i',
        'Sabato',
        'Domenica',
    ],
    'en': [
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday',
    ],
}

# these are properly Latex-escaped strings where needed
monthNamesPerLanguage = {
    'it': [
        'Gennaio',
        'Febbraio',
        'Marzo',
        'Aprile',
        'Maggio',
        'Giugno',
        'Luglio',
        'Agosto',
        'Settembre',
        'Ottobre',
        'Novembre',
        'Dicembre',
    ],
    'en': [
        'January',
        'February',
        'March',
        'April',
        'May',
        'June',
        'July',
        'August',
        'September',
        'October',
        'November',
        'December',
    ],
}

admittedImageMimeTypeToExtension = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
}

availableLanguages = [
    ('en', 'English'),
    ('it', 'Italian'),
]

startingWeekdayChoices = [
    ('6', 'Sunday'),
    ('0', 'Monday'),
]

monthChoices = [
    ('1', 'Jan'),
    ('2', 'Feb'),
    ('3', 'Mar'),
    ('4', 'Apr'),
    ('5', 'May'),
    ('6', 'Jun'),
    ('7', 'Jul'),
    ('8', 'Aug'),
    ('9', 'Sep'),
    ('10', 'Oct'),
    ('11', 'Nov'),
    ('12', 'Dec'),
]

languageMap = dict(availableLanguages)
startingWeekdayMap = dict(startingWeekdayChoices)

pdfGenerationTimeoutSeconds = 15
