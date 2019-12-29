""" textImageTools.py
    Tools to handle the retrieval and serving
    of text-as-images (e.g. DPO email, contact, ...).
"""

import os

from flask import (
    send_from_directory,
    abort,
)

from ostracion_app.utilities.fileIO.thumbnails import (
    createTransparentTextImage,
    determineManagedTextImagePath,
)


def prepareTextualImageForView(db, user, imgText, imgPrefix):
    """ Given a text and its (tag) prefix, either return (and serve) the
        image containing the text or abort with 404.

        Takes care of rebuilding the image if not built already.
    """
    imgFilePath, imgFileTitle, _ = determineManagedTextImagePath(
        imgText,
        prefix=imgPrefix,
    )
    imgFileName = os.path.join(
        imgFilePath,
        imgFileTitle,
    )
    print('imgFileName ',imgFileName)
    if (os.path.isfile(imgFileName) or
            createTransparentTextImage(
                imgText,
                imgFileName,
            )):
        return send_from_directory(
            imgFilePath,
            imgFileTitle,
            mimetype='image/png',
        )
    else:
        return abort(404)
