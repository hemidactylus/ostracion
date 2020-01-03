""" errors.py
    Error-handler routes
"""

from flask import (
    redirect,
    request,
    url_for,
)

from ostracion_app.app_main import app

from ostracion_app.utilities.viewTools.messageTools import flashMessage

from ostracion_app.utilities.exceptions.exceptions import (
    OstracionWarning,
    OstracionError,
    exceptionToFlashable,
)


# @app.errorhandler(Exception)
# def exceptionHandler(error):
#     """ Generic catcher for in-route errors.
#         Handles all exceptions, in particular through the
#         use of the 'exceptions' module they end up as flashed information.

#         Preferentially redirects to request._onErrorUrl if it is set,
#         otherwise falls back to "index".
#     """
#     flashableError = exceptionToFlashable(error)
#     flashMessage(**flashableError)
#     if hasattr(request, '_onErrorUrl'):
#         return redirect(request._onErrorUrl)
#     else:
#         return redirect(url_for('lsView'))
