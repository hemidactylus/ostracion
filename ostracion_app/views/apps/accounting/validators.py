"""
    validators.py
        Accounting-specific validators
"""

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
