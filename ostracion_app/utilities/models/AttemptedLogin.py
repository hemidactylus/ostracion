""" AttemptedLogin.py
    class for DB object "attempted login".
"""

from ostracion_app.utilities.models.DictableObject import DictableObject


class AttemptedLogin(DictableObject):
    namedFields = ['sender_hash', 'datetime']

    def __init__(self, **kwargs):
        """Standard 'DictableObject' init."""
        _kwargs = self.consumeKWargs(**kwargs)
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )

    def __repr__(self):
        return '<AttemptedLogin "%s" (%s)>' % (
            self.sender_hash,
            self.datetime.strftime('%Y-%m-%d %H:%M:%S')
        )
