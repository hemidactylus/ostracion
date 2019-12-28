""" User.py
    Class representing 'user' rows from DB.
"""

import hashlib

from ostracion_app.utilities.tools.securityCodes import makeSecurityCode

from ostracion_app.utilities.models.DictableObject import DictableObject


class User(DictableObject):
    namedFields = ['username', 'fullname', 'salt', 'passwordhash', 'email',
                   'icon_file_id', 'icon_file_id_username', 'icon_mime_type',
                   'banned', 'last_login']

    def __init__(self, **kwargs):
        """ Standard 'DictableObject' init, plus delicate handling of:
            - password being given instead of passwordHash e.g. when creating
              the user as opposed to when reading from DB.
            - refreshing of the salt in the latter case, i.e. when password
              is given (i.e. when new user or password change), we regenerate
              a salt and re-hash the password.
            * This may get cumbersome in the future since it is philosophically
              incorrect to seal such logic in this class.
        """
        for optF in {'icon_mime_type'}:
            if optF not in kwargs:
                kwargs[optF] = ''
        for optNulF in {'last_login'}:
            if optNulF not in kwargs:
                kwargs[optNulF] = None
        if 'password' in kwargs and 'salt' in kwargs:
            # on password change we force re-salt
            del kwargs['salt']
        if 'salt' not in kwargs:
            kwargs['salt'] = makeSecurityCode(nSyllables=8)
        _kwargs = self.consumeKWargs(**kwargs)
        if 'password' in _kwargs:
            self.passwordhash = self._hashString(
                _kwargs['password'] + kwargs['salt']
            )
            del _kwargs['password']
        if _kwargs:
            raise ValueError(
                'Unknown argument(s): %s' % ', '.join(_kwargs.keys())
            )
        #
        self.roles = None

    @staticmethod
    def _hashString(message):
        return hashlib.sha256(message.encode()).hexdigest()

    def checkPassword(self, stringToCheck):
        return self._hashString(stringToCheck + self.salt) == self.passwordhash

    @property
    def is_authenticated(self):
        """ True unless the object represents a user that should
            not be allowed to authenticate for some reason.
        """
        return True

    @property
    def is_active(self):
        """ True for users unless they are inactive,
            for example because they have been banned.

            NOTE: Ostracion handles banning outside of this logic,
            i.e. by hand.
        """
        return True

    @property
    def is_anonymous(self):
        """ True only for fake users that are not
            supposed to log in to the system.

            NOTE: Ostracion handles 'anonymous' users
            in a very different way from this property.
        """
        return False

    def setRoles(self, roles):
        self.roles = roles

    def has_role(self, roleId):
        return (
            self.roles is not None and
            any(r.role_id == roleId for r in self.roles)
        )

    def get_id(self):
        """ Unique identifier for the user,
            in unicode format (or 'str' in python3).
        """
        return str(self.username)

    def getName(self):
        return self.fullname

    def __lt__(self, other):
        return self.username < other.username

    def __repr__(self):
        return '<User "%s" (%s)>' % (self.username, self.fullname)
