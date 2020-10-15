"""
    forms.py
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    BooleanField,
    SubmitField,
    RadioField,
    HiddenField,
    SelectField,
    PasswordField,
    TextAreaField,
    FormField,
    FieldList,
    Form,
)


monthChoices = [
    ('1', 'Jan'),
    ('2', 'Feb'),
    ('3', 'Mar'),
    ('12', 'Dec'),
]

class CalendarMakerPropertyForm(FlaskForm):
    month0 = SelectField('StartMonth', choices=monthChoices)
    year0 = StringField('StartYear')
    month1 = SelectField('EndMonth', choices=monthChoices)
    year1 = StringField('EndYear')
    language = SelectField('Language', choices=[('en', 'English'), ('it', 'Italian')])
    submit = SubmitField('Set')
