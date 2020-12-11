"""
    forms.py
        Accounting-specific forms
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    SelectField,
)

from wtforms.validators import (
    InputRequired,
)

from ostracion_app.utilities.forms.validators.validators import (
    CharacterSelector,
)

from ostracion_app.views.apps.accounting.validators import ProhibitedIDChoice


class AccountingBaseLedgerForm(FlaskForm):
    """Basic ledger properties form"""
    ledgerId = StringField(
        'ledgerId',
        validators=[InputRequired(), CharacterSelector()],
    )
    name = StringField('name', validators=[InputRequired()])
    description = StringField('description')
    submit = SubmitField('Save')


class AccountingLedgerActorForm(FlaskForm):
    """A single-actor-form for a ledger"""
    actorId = StringField(
        'actorId',
        validators=[InputRequired(), CharacterSelector()],
    )
    name = StringField('name', validators=[InputRequired()])
    submit = SubmitField('Add')


class AccountingLedgerCategoryForm(FlaskForm):
    """A category-form for a ledger"""
    categoryId = StringField(
        'categoryId',
        validators=[InputRequired(), CharacterSelector()],
    )
    description = StringField('description')
    submit = SubmitField('Add')


class AccountingLedgerSubcategoryForm(FlaskForm):
    """A subcategory-form for a ledger. Here the category is
       from a dynamic selection"""
    categoryId = SelectField('Category', default='',
                             validators=[
                                ProhibitedIDChoice(
                                    message='Please choose one',
                                ),
                             ])
    subcategoryId = StringField(
        'subcategoryId',
        validators=[InputRequired(), CharacterSelector()],
    )
    description = StringField('description')
    submit = SubmitField('Add')

    def fillCategoryChoices(self, choices):
        self.categoryId.choices = ([('', 'Choose category...')]
                                   + [(cId, cId) for cId in choices])
