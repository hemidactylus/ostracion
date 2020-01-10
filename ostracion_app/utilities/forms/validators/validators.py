""" validators.py:
    custom validators for use by the flask forms.
"""

from wtforms.validators import ValidationError, StopValidation, InputRequired

from ostracion_app.utilities.tools.comparisonTools import (
    optionNumberLeq,
)

from ostracion_app.utilities.tools.setNaming import (
    humanFriendlyDescribeCharacterSet,
)


_defaultCharSet = set(
    '1234567890qwertyuiopasdfghjklzxcvbnmPOIUYTREWQLKJHGFDSAMNBVCXZ_-.'
)


class ConstrainedOptionalInt():
    """<Empty string or integer not greater than ...> validator."""
    def __init__(self, maxValue, message=None):
        self.maxValue = maxValue
        if message is None:
            self.message = 'Invalid value'
        else:
            self.message = message

    def __call__(self, form, field):
        try:
            optValue = int(field.data) if field.data.strip() != '' else None
            if not optionNumberLeq(self.maxValue, optValue):
                raise ValidationError(self.message)
        except Exception:
            raise ValidationError(self.message)


class CharacterSelector():
    """<Some chars allowed> validator."""
    def __init__(self, characterSet=_defaultCharSet, message=None):
        self.characterSet = characterSet
        if message is None:
            self.message = 'Invalid identifier. Valid characters: %s .' % (
                humanFriendlyDescribeCharacterSet(self.characterSet)
            )
        else:
            self.message = message

    def __call__(self, form, field):
        if any(c not in self.characterSet for c in field.data):
            raise ValidationError(self.message)


class MinimumLength():
    """<Minumum text length> validator."""
    def __init__(self, minLength, message=None):
        self.minLength = minLength
        if message is None:
            self.message = 'At least %i characters' % minLength
        else:
            self.message = message

    def __call__(self, form, field):
        if len(field.data) < self.minLength:
            raise ValidationError(self.message)


class NonnegativeInteger():
    """<zero or positive integer as a string> validator."""
    def __init__(self, message=None):
        if message is None:
            self.message = 'Must be zero or a positive integer'
        else:
            self.message = message

    def __call__(self, form, field):
        if field.data.strip() != '':
            try:
                v = int(field.data)
                if v < 0:
                    raise ValidationError(self.message)
            except Exception:
                raise ValidationError(self.message)


class PositiveInteger():
    """<positive integer as a string> validator."""
    def __init__(self, message=None):
        if message is None:
            self.message = 'Must be a positive integer'
        else:
            self.message = message

    def __call__(self, form, field):
        if field.data.strip() != '':
            try:
                v = int(field.data)
                if v < 1:
                    raise ValidationError(self.message)
            except Exception:
                raise ValidationError(self.message)


class OptionalInteger():
    """<empty string or integer as a string> validator."""
    def __init__(self, message=None):
        if message is None:
            self.message = 'Insert a number or leave empty'
        else:
            self.message = message

    def __call__(self, form, field):
        if field.data is not None and field.data.strip() != '':
            try:
                v = int(field.data)
            except Exception:
                raise ValidationError(self.message)


class ColorString():
    """<6-digit hexcolor as a string> validator."""
    def __init__(self, allowEmpty=True, poundOptional=True, message=None):
        self.allowEmpty = allowEmpty
        self.poundOptional = poundOptional
        if message is None:
            self.message = 'Invalid color'
        else:
            self.message = message

    def __call__(self, form, field):
        s = field.data
        if len(s) == 0:
            if not self.allowEmpty:
                raise ValidationError(self.message)
        else:
            # non-empty color string
            if s[0] != '#':
                colString = s
                if not self.poundOptional:
                    raise ValidationError(self.message)
            else:
                colString = s[1:]
            # check on colString
            if (len(colString) != 6 or
                    len(set(colString.lower()) - set('1234567890abcdef')) > 0):
                raise ValidationError(self.message)
