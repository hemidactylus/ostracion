""" textFileViewingModes.py
    here the various viewing modes
    of text files are registered
    for use throughout the app.

    The 'content mode preparers' are functions
    each accepting a file, a mode (ticket/gallery, usually discarded
    for text files since there is no need for different source-image URLs),
    some view parameters (also discarded in most cases) and the fileStorageDir
    for retrieving source files.
    The returned dict is passed on to the rendering template for file-view.
"""

from ostracion_app.utilities.fileIO.physical import (
    fileIdToPath,
)

from ostracion_app.utilities.tools.markdownTools import (
    markdownToHtml,
)


def plainTextFileContentModePreparer(file, mode, viewParameters,
                                     fileStorageDirectory):
    """Return a plain-text file."""
    fileContents = {
        'mode': 'plain',
        'value': open(fileIdToPath(
            file.file_id,
            fileStorageDirectory=fileStorageDirectory,
        )).read(),
    }
    return fileContents


def markdownTextFileContentModePreparer(file, mode, viewParameters,
                                        fileStorageDirectory):
    """Read the source text, make it markdown and return the resulting DOM."""
    fileContents = {
        'mode': 'markdown',
        'value': markdownToHtml(
            open(fileIdToPath(
                file.file_id,
                fileStorageDirectory=fileStorageDirectory,
            )).read(),
            replacements=[],
        ),
    }
    return fileContents


textFileViewingModes = {
    'plain': {
        'index': 0,
        'title': 'Plain',
        'contentPreparer': plainTextFileContentModePreparer,
    },
    'markdown': {
        'index': 1,
        'title': 'Markdown',
        'contentPreparer': markdownTextFileContentModePreparer,
    },
}
