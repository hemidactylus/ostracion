"""
    forms.py
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
)

from wtforms.validators import (
    InputRequired,
)

from ostracion_app.utilities.forms.validators.validators import (
    CharacterSelector,
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
    """A sigle-actor-form for a ledger"""
    actorId = StringField(
        'actorId',
        validators=[InputRequired(), CharacterSelector()],
    )
    name = StringField('name', validators=[InputRequired()])
    submit = SubmitField('Add')
