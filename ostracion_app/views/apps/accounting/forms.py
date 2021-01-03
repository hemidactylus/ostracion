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
    OptionalPositiveInteger,
    OptionalFloat,
)

from ostracion_app.views.apps.accounting.validators import (
    ProhibitedIDChoice,
    ValidDateTime,
)

from ostracion_app.views.apps.accounting.settings import (
    ledgerDatetimeFormat,
    ledgerDatetimeFormatDesc,
)


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


def generateAccountingMovementForm(categoryTree, actors):
    """ Generate a form for a movement in a particular accounting ledger."""

    class _aForm(FlaskForm):
        submit = SubmitField('+')
        date = StringField(
            'Date',
            validators=[ValidDateTime(
                ledgerDatetimeFormat,
                'Insert a valid "%s" date' % ledgerDatetimeFormatDesc,
            )],
        )
        description = StringField('Description')
        categoryId = SelectField(
            'Category',
            default='',
            validators=[
                ProhibitedIDChoice(
                    message='Please choose one',
                ),
            ],
            choices=(
                [('', 'Choose category...')] + [
                    (
                        catO['category'].category_id,
                        catO['category'].category_id,
                    )
                    for catO in categoryTree
                ]
            ),
        )
        subcategoryId = SelectField(
            'Subcategory',
            default='',
            validators=[
                ProhibitedIDChoice(
                    message='Please choose one',
                ),
            ],
            choices=(
                [('', 'Choose subcategory...')] + [
                    (
                        '%s.%s' % (
                            catO['category'].category_id,
                            subcat.subcategory_id,
                        ),
                        subcat.subcategory_id,
                    )
                    for catO in categoryTree
                    for subcat in catO['subcategories']
                ]
            ),
        )
    #
    for actor in actors:
        actorName = actor.name
        actorPaidId = 'actorpaid_%s' % actor.actor_id
        actorPropId = 'actorprop_%s' % actor.actor_id

        paidField = StringField(
            '%s (paid)' % actorName,
            validators=[OptionalFloat(admitCommas=True)]
        )
        propField = StringField(
            '%s (prop)' % actorName,
            validators=[OptionalPositiveInteger()]
        )
        setattr(_aForm, actorPaidId, paidField)
        setattr(_aForm, actorPropId, propField)

    return _aForm()
