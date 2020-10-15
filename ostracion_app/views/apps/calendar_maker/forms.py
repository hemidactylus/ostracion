"""
    forms.py
"""

from flask_wtf import FlaskForm
from wtforms import (
    # StringField,
    IntegerField,
    SubmitField,
    SelectField,
    # Form,
)

from wtforms.validators import (
    InputRequired,
    NumberRange,
    # DataRequired,
    # Required,
    # EqualTo,
    # Length,
)


monthChoices = [
    ('1', 'Jan'),
    ('2', 'Feb'),
    ('3', 'Mar'),
    ('12', 'Dec'),
]

class CalendarMakerPropertyForm(FlaskForm):
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
        choices=[('en', 'English'), ('it', 'Italian')],
    )
    submit = SubmitField('Set')
