""" OstracionAnonymousUser.py
    A class for anonymous users to provide the login manager.
"""

from flask_login import AnonymousUserMixin

from ostracion_app.utilities.userTools.anonymousRole import (
    anonymousRoleDict,
)

from ostracion_app.utilities.models.Role import Role


class OstracionAnonymousUser(AnonymousUserMixin):

    def __init__(self):
        """ Initialise the custom anonymous user instance,
            delegating to super.
        """
        AnonymousUserMixin.__init__(self)
        self.roles = [Role(**anonymousRoleDict)]

    @property
    def username(self):
        """ Provide non-logged-in users with the empty-string username,
            to achieve compatibility with the various places where
            this is handy.
        """
        return ''
