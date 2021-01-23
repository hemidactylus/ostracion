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
    categoryIdsCharacterSet,
)


def _makeCategorySelect(categoryTree, allowNone):
    """Create a select field with values read off the input."""
    if allowNone:
        vals = []
    else:
        vals = [
            ProhibitedIDChoice(
                message='Please choose one',
            ),
        ]
    #
    return SelectField(
        'Category',
        default='',
        validators=vals,
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


def _makeSubcategorySelect(categoryTree, allowNone):
    """Create a select field with values read off the input."""
    if allowNone:
        vals = []
    else:
        vals = [
            ProhibitedIDChoice(
                message='Please choose one',
            ),
        ]
    #
    return SelectField(
        'Subcategory',
        default='',
        validators=vals,
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


class AccountingBaseLedgerForm(FlaskForm):
    """Basic ledger properties form"""
    ledgerId = StringField(
        'ledgerId',
        validators=[
            InputRequired(),
            CharacterSelector(characterSet=categoryIdsCharacterSet),
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
            CharacterSelector(characterSet=categoryIdsCharacterSet),
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
            CharacterSelector(characterSet=categoryIdsCharacterSet),
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
            CharacterSelector(characterSet=categoryIdsCharacterSet),
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
        submit = SubmitField('Apply filters')
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
        description = StringField('Description')
        categoryId = _makeCategorySelect(categoryTree, allowNone=True)
        subcategoryId = _makeSubcategorySelect(categoryTree, allowNone=True)

        def receiveValues(self, query):
            """Use the values in 'query' to set field data."""
            if 'dateFrom' in query:
                self.dateFrom.data = query['dateFrom'].strftime(
                    ledgerDatetimeFormat,
                )
            if 'dateTo' in query:
                self.dateTo.data = query['dateTo'].strftime(
                    ledgerDatetimeFormat,
                )
            if 'description' in query:
                self.description.data = query['description']
            if 'categoryId' in query:
                self.categoryId.data = query['categoryId']
                if 'subcategoryId' in query:
                    self.subcategoryId.data = '%s.%s' % (
                        query['categoryId'],
                        query['subcategoryId'],
                    )
                else:
                    self.subcategoryId.data = ''
            else:
                self.categoryId.data = ''
                self.subcategoryId.data = ''

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
        categoryId = _makeCategorySelect(categoryTree, allowNone=False)
        subcategoryId = _makeSubcategorySelect(categoryTree, allowNone=False)
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
