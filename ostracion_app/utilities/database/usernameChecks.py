""" usernameChecks.py
    tools to deal with existing-/prospect-username checks
"""

from ostracion_app.utilities.database.userTools import (
    dbGetUser,
)

from ostracion_app.utilities.database.tickets import (
    enrichTicket,
    dbGetAllUserInvitationTickets,
)


def isUsername(db, username, user):
    """Checks if the proposed username is not already existing."""
    return dbGetUser(db, username) is not None


def isProspectedUsername(db, username, user, urlRoot):
    """ Check if a psoposed username is not existing
        nor it is going to exist upon redemption of a valid
        user-invitation ticket with constrained username.

        Used in the user creation through tickets.
    """
    if not isUsername(db, username, user):
        return any(
            t['redeemable'] and t['metadata'].get('username') == username
            for t in (
                enrichTicket(db, _t, urlRoot=urlRoot)
                for _t in dbGetAllUserInvitationTickets(
                    db,
                    user,
                )
            )
        )
    else:
        return True
