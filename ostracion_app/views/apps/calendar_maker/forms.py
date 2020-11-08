"""
    forms.py
"""

from flask_wtf import FlaskForm
from wtforms import (
    IntegerField,
    SubmitField,
    SelectField,
)

from wtforms.validators import (
    InputRequired,
    NumberRange,
)


from ostracion_app.views.apps.calendar_maker.engine.settings import (
    availableLanguages,
    startingWeekdayChoices,
    monthChoices,
)


class CalendarMakerPropertyForm(FlaskForm):
    """Calendar settings form (class)."""
    month0 = SelectField('StartMonth', choices=monthChoices)
    year0 = IntegerField(
        'StartYear',
        validators=[InputRequired(), NumberRange(min=1900, max=2100)],
    )
    month1 = SelectField('EndMonth', choices=monthChoices)
    year1 = IntegerField(
        'EndYear',
        validators=[InputRequired(), NumberRange(min=1900, max=2100)],
    )
    language = SelectField(
        'Language',
        choices=availableLanguages,
    )
    startingweekday = SelectField(
        'Starting weekday',
        choices=startingWeekdayChoices,
    )
    submit = SubmitField('Set')
