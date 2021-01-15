"""
    validators.py
        Accounting-specific validators
"""

import datetime

from wtforms.validators import ValidationError, StopValidation, InputRequired


class ProhibitedIDChoice():
    """Some IDs in a SelectField are not allowed."""
    def __init__(self, forbiddenIds={""}, message=None):
        self.forbiddenIds = forbiddenIds
        if message is None:
            self.message = 'Invalid choice'
        else:
            self.message = message

    def __call__(self, form, field):
        if field.data in self.forbiddenIds:
            raise ValidationError(self.message)


class ValidDateTime():
    """Constrained date/time format"""
    def __init__(self, datetimeFormat='%Y/%m/%d', message=None,
                 optional=False):
        self.datetimeFormat = datetimeFormat
        self.optional = optional
        if message is None:
            self.message = (
                'Invalid date/time format. Use "%s"' % datetimeFormat
            )
        else:
            self.message = message

    def __call__(self, form, field):
        if not isinstance(field.data, str):
            raise ValidationError(self.message)
        else:
            if self.optional and field.data == '':
                # empty-string is allowed if optional
                pass
            else:
                try:
                    datetime.datetime.strptime(field.data, self.datetimeFormat)
                except ValueError:
                    raise ValidationError(self.message)
