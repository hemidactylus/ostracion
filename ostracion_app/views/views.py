"""
    views.py
"""

from datetime import datetime

from flask import (
    render_template,
    redirect,
    session,
    url_for,
    request,
    g,
    send_from_directory,
)
from flask_bootstrap import Bootstrap

from ostracion_app.app_main import app

from ostracion_app.utilities.database.dbTools import (
    dbGetDatabase,
)

Bootstrap(app)


@app.route('/index')
@app.route('/')
def indexView():
    """Standard redirects."""
    return redirect(url_for('lsView'))
