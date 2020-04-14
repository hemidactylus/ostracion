""" app_main.py:
    Main entry point which creates the Flask app and loads routes.
"""

import os
from flask import Flask

from config import (
    templateDirectory,
    staticDirectory,
)
#
from sensitive_config import (
    SECRET_KEY,
)

app = Flask(
    'ostracion',
    static_folder=staticDirectory,
    static_url_path='/static',
    template_folder=templateDirectory,
)
app.config.update(
    WTF_CSRF_ENABLED=True,
    SECRET_KEY=SECRET_KEY,
)

# this must be AFTER the above, to prevent circular imports
# (even if this formally violates PEP8)
import ostracion_app.views.views
import ostracion_app.views.logins
import ostracion_app.views.thumbnails
import ostracion_app.views.uploads
import ostracion_app.views.fileaccess
import ostracion_app.views.links
import ostracion_app.views.boxaccess
import ostracion_app.views.admin
import ostracion_app.views.userprofile
import ostracion_app.views.info
import ostracion_app.views.tickets
import ostracion_app.views.find
import ostracion_app.views.errors
import ostracion_app.views.tools
import ostracion_app.views.archives
