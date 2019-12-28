""" messageTools.py
    Flashing messages on the web app.
"""

from flask import (
    flash,
)

messageClassNormalizer = {
    'Info': 'info',
    'Error': 'danger',
    'Warning': 'warning',
    'Success': 'success',
}


def flashMessage(msgClass=None, msgHeading='', msgBody=None, pillText=None):
    """Enqueue a flashed structured message for use by the render template."""
    nMsgClass = messageClassNormalizer.get(msgClass, 'primary')
    if msgBody is not None:
        flash({
            'class': nMsgClass,
            'heading': msgHeading,
            'body': msgBody,
            'pillText': pillText,
        })
