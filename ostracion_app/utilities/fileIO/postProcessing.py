""" postProcessing.py :

    generic operations tied to file
    analysis - for use by the uploading process.
"""

import os
import magic


def determineFileProperties(filepath):
    """ Given a path to a stored file, determine
        properties such as size and file (mime/)type.
    """
    fileType = {
        'file_type': '',
        'file_mime_type': '',
        'file_size': 0,
    }
    try:
        fileType['file_type'] = magic.from_file(filepath)
    except Exception:
        pass
    try:
        fileType['file_mime_type'] = magic.from_file(filepath, mime=True)
    except Exception:
        pass
    try:
        fileType['file_size'] = os.stat(filepath).st_size
    except Exception:
        pass
    #
    return fileType
