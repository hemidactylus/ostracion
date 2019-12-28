'''
    loginTools.py
'''


def loginTitle(g):
    """Title of login view."""
    return 'Login'


def loginSubtitle(g):
    """Subtitle of login view."""
    appShortName = g.settings['behaviour']['behaviour_appearance'][
      'application_short_name']['value']
    return 'Enter your credentials for %s' % appShortName


def logoutTitle(g):
    """Title of logout view."""
    return 'Logout'


def logoutSubtitle(g):
    """Subtitle of logout view."""
    appShortName = g.settings['behaviour']['behaviour_appearance'][
      'application_short_name']['value']
    return 'Close your user\'s session with %s' % appShortName
