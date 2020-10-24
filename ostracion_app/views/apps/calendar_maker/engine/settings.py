"""
    settings.py
"""

admittedImageMimeTypes = {
    'image/gif', 
    'image/jpeg', 
    'image/png', 
}

availableLanguages = [
    ('en', 'English'),
    ('it', 'Italian'),
]

startingWeekdayChoices = [('6', 'Sunday'), ('0' ,'Monday')]

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
