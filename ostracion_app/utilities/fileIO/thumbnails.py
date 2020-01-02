""" thumbnails.py
    resolution of a file's appropriate thumbnail from its MIME type
    (thumbnail chosen among the statically configured ones).
"""

import hashlib
import shutil
import subprocess
from uuid import uuid4

from ostracion_app.utilities.fileIO.postProcessing import (
    determineFileProperties,
)

from ostracion_app.utilities.fileIO.physical import (
    fileIdToPath,
)

from config import staticFileIconsRootPath

from ostracion_app.utilities.fileIO.mimeTypeMaps import (
    mimeTypeToDefaultThumbnailMap,
    imageMimeTypeToResizeMethodMap,
)

from config import (
    managedImagesDirectory,
)

thumbnailFormatMap = {
    'thumbnail': {
        'x': 320,
        'y': 320,
    },
    'logo_small': {
        'x': 60,
        'y': 60,
    },
    'landscape': {
        'x': 800,
        'y': 600,
    },
    'free': {
        'x': None,
        'y': None
    },
}


def makeResizeGeometryStringArgs(sizeClass):
    """Prepare the arguments for 'thumbnail' and 'size' to invoke convert."""
    fmtMap = thumbnailFormatMap[sizeClass]
    x, y = fmtMap['x'], fmtMap['y']
    if x is None or y is None:
        return None, None
    else:
        return '%ix%i^' % (x, y), '%ix%i' % (x, y)


def pickFileThumbnail(mime_type):
    """Generate the static path of a file-icon based on its mime type."""
    return '/%s/%s.png' % (
        staticFileIconsRootPath,
        mimeTypeToDefaultThumbnailMap.get(mime_type, 'other/other'),
    )


def isImageMimeType(mime_type):
    """Is this mime type that of an image?"""
    return mime_type in imageMimeTypeToResizeMethodMap


def makeFileThumbnail(srcFileId, mimeType,
                      thumbnailFormat, fileStorageDirectory):
    """Given an image file, extract a thumbnail out of it."""
    resizeMethod = imageMimeTypeToResizeMethodMap.get(mimeType)
    if resizeMethod == 'resize':
        newId = uuid4().hex
        if resizeToThumbnail(
            fileIdToPath(srcFileId, fileStorageDirectory=fileStorageDirectory),
            fileIdToPath(newId, fileStorageDirectory=fileStorageDirectory),
            thumbnailFormat=thumbnailFormat,
        ):
            return newId, mimeType
        else:
            return None, None
    elif resizeMethod == 'copy':
        newId = uuid4().hex
        shutil.copy(
            fileIdToPath(srcFileId, fileStorageDirectory=fileStorageDirectory),
            fileIdToPath(newId, fileStorageDirectory=fileStorageDirectory),
        )
        return newId, mimeType
    elif resizeMethod is None:
        # if mime type not enumerated, fail and that's it
        return None, None
    else:
        raise NotImplementedError(
            'resize method not supported: "%s"' % resizeMethod
        )


def makeTempFileIntoThumbnail(tmpFileFullPath, thumbnailFormat,
                              fileStorageDirectory):
    """Given a temporarily saved file, prepare and store a thumbnail."""
    mimeType = determineFileProperties(tmpFileFullPath).get('file_mime_type')
    resizeMethod = imageMimeTypeToResizeMethodMap.get(mimeType)
    if resizeMethod == 'resize':
        newId = uuid4().hex
        if resizeToThumbnail(
            tmpFileFullPath,
            fileIdToPath(newId, fileStorageDirectory=fileStorageDirectory),
            thumbnailFormat=thumbnailFormat,
        ):
            return newId, mimeType
    elif resizeMethod == 'copy':
        newId = uuid4().hex
        shutil.copy(
            tmpFileFullPath,
            fileIdToPath(newId, fileStorageDirectory=fileStorageDirectory),
        )
        return newId, mimeType
    else:
        # if mime type not listed, fail and that's it
        return None, None


def resizeToThumbnail(srcFile, dstFile, thumbnailFormat):
    """ Resize a file (srcFile -> dstFile, actual filename paths)
        according to the thumbnail format specified.
        Return True upon success.
    """
    rThumbArg, rExtentArg = makeResizeGeometryStringArgs(thumbnailFormat)
    resizingOutput = subprocess.run(
        [
            arg
            for arg in (
                'convert',
                srcFile,
                '-auto-orient',  # against in-picture rotation info for thb.
                '-thumbnail' if rThumbArg is not None else None,
                rThumbArg if rThumbArg is not None else None,
                '-gravity',
                'center',
                '-extent' if rExtentArg is not None else None,
                rExtentArg if rExtentArg is not None else None,
                # '-flatten',   # that would make animated GIFs collapse to one
                '-strip',       # removal of EXIF data
                dstFile,
            )
            if arg is not None
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return resizingOutput.returncode == 0


def determineManagedTextImagePath(txt, prefix=''):
    """ Given a text, construct the
        path/filename/hashed-tag of the text-image.
    """
    textTag = hashlib.sha256(('%s%s' % (prefix, txt)).encode()).hexdigest()
    fileTitle = '%s.png' % textTag
    filePath = managedImagesDirectory
    return filePath, fileTitle, textTag


def createTransparentTextImage(text, destFileName):
    """ Create an image containing the given
        text and transparent background.

        Returns True iff success.
    """
    imageCreationOutput = subprocess.run(
        [
            'convert',
            '-background',
            'transparent',
            '-size',
            '10000x200',
            '-gravity',
            'Center',
            '-weight',
            '700',
            '-pointsize',
            '200',
            '-kerning',
            '10',
            '-font',
            'Courier-Bold',
            'caption:%s' % text,
            '-trim',
            '%s' % destFileName,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return imageCreationOutput.returncode == 0
