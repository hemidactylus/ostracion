#!/usr/bin/env python

"""
    A simple script to start the app on the local machine
    with one process, no reverse proxy etc.
"""

import sys

from ostracion_app.app_main import app

if __name__ == '__main__':
    # if -e flag is specified, enable running as
    # externally-accessible (still non-production) host
    host = None
    if '-e' in sys.argv[1:]:
        host = '0.0.0.0'
    app.run(debug=True, host=host)
