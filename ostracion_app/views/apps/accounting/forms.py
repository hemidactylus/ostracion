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
    Length,
)

from config import (
    maxShortIdentifierLength,
    maxIdentifierLength,
)

from ostracion_app.utilities.forms.validators.validators import (
    CharacterSelector,
    OptionalPositiveInteger,
    OptionalFloat,
    AtLeastOneNonempty,
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
        validators=[
            InputRequired(),
            CharacterSelector(),
            Length(max=maxShortIdentifierLength),
        ],
    )
    name = StringField(
        'name',
        validators=[
            InputRequired(),
            Length(max=maxShortIdentifierLength)
        ],
    )
    description = StringField(
        'description',
        validators=[Length(max=maxIdentifierLength)],
    )
    submit = SubmitField('Save')


class AccountingLedgerActorForm(FlaskForm):
    """A single-actor-form for a ledger"""
    actorId = StringField(
        'actorId',
        validators=[
            InputRequired(),
            CharacterSelector(),
            Length(max=maxShortIdentifierLength),
        ],
    )
    name = StringField(
        'name',
        validators=[InputRequired(), Length(max=maxShortIdentifierLength)],
    )
    submit = SubmitField('Add')


class AccountingLedgerCategoryForm(FlaskForm):
    """A category-form for a ledger"""
    categoryId = StringField(
        'categoryId',
        validators=[
            InputRequired(),
            CharacterSelector(),
            Length(max=maxShortIdentifierLength),
        ],
    )
    description = StringField(
        'description',
        validators=[Length(max=maxIdentifierLength)],
    )
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
        validators=[
            InputRequired(),
            CharacterSelector(),
            Length(max=maxShortIdentifierLength),
        ],
    )
    description = StringField(
        'description',
        validators=[
            Length(max=maxIdentifierLength)
        ],
    )
    submit = SubmitField('Add')

    def fillCategoryChoices(self, choices):
        self.categoryId.choices = ([('', 'Choose category...')]
                                   + [(cId, cId) for cId in choices])


def generateAccountingLedgerQueryForm(categoryTree, actors):
    """ Generate a form for queries on the ledger movements."""

    class _qForm(FlaskForm):
        submit = SubmitField('Search')
        dateFrom = StringField(
            'Date',
            validators=[
                ValidDateTime(
                    ledgerDatetimeFormat,
                    'Insert a valid "%s" date' % ledgerDatetimeFormatDesc,
                    optional=True,
                ),
                Length(max=maxShortIdentifierLength),
            ],
        )
        dateTo = StringField(
            'Date',
            validators=[
                ValidDateTime(
                    ledgerDatetimeFormat,
                    'Insert a valid "%s" date' % ledgerDatetimeFormatDesc,
                    optional=True,
                ),
                Length(max=maxShortIdentifierLength),
            ],
        )

    return _qForm()


def generateAccountingMovementForm(categoryTree, actors):
    """ Generate a form for a movement in a particular accounting ledger."""

    class _aForm(FlaskForm):
        submit = SubmitField('+')
        date = StringField(
            'Date',
            validators=[
                ValidDateTime(
                    ledgerDatetimeFormat,
                    'Insert a valid "%s" date' % ledgerDatetimeFormatDesc,
                ),
                Length(max=maxShortIdentifierLength),
            ],
        )
        description = StringField(
            'Description',
            validators=[Length(max=maxIdentifierLength)],
        )
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
    paidFields = {}
    propFields = {}
    # standard validators for all such fields
    baseValidators = [
        OptionalFloat(admitCommas=True),
        Length(max=maxShortIdentifierLength),
    ]
    #
    for actorIndex, actor in enumerate(actors):
        actorName = actor.name
        actorPaidId = 'actorpaid_%s' % actor.actor_id
        actorPropId = 'actorprop_%s' % actor.actor_id

        if actorIndex == len(actors) - 1:
            # for the last of the paid forms, a collective validator
            finalValidators = [
                AtLeastOneNonempty(list(paidFields.keys())),
            ]
        else:
            finalValidators = []

        paidFields[actorPaidId] = StringField(
            '%s (paid)' % actorName,
            validators=baseValidators + finalValidators,
        )
        propFields[actorPropId] = StringField(
            '%s (prop)' % actorName,
            validators=[
                OptionalPositiveInteger(),
                Length(max=maxShortIdentifierLength),
            ],
        )
        setattr(_aForm, actorPaidId, paidFields[actorPaidId])
        setattr(_aForm, actorPropId, propFields[actorPropId])

    return _aForm()
