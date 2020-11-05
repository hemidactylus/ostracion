""" physical.py:
    tools to translate abstract file IDs
    to physical paths on the actual filesystem.
"""

import os
from uuid import uuid4


def fileIdToSplitPath(fileId, fileStorageDirectory):
    """Given a file ID, create dir,filename on actual FS."""
    subdirBlock = (fileId+'0000')[:4]
    sd1, sd2 = subdirBlock[0:2], subdirBlock[2:4]
    finalDir = os.path.join(
        fileStorageDirectory,
        sd1,
        sd2,
    )
    mkDirP(finalDir)
    #
    return (
        finalDir,
        fileId,
    )


def fileIdToPath(fileId, fileStorageDirectory):
    """Same as fileIdToSplitPath but joined in a fullpath string."""
    return os.path.join(
        *fileIdToSplitPath(fileId, fileStorageDirectory),
    )


def temporarySplitFileName(tempFileDirectory):
    """
        Generate a fullpath temporary filename,
        returnig it in the form (directory, filetitle)
    """
    mkDirP(tempFileDirectory)
    return (
        tempFileDirectory,
        uuid4().hex,
    )


def temporaryFileName(tempFileDirectory):
    """Generate a fullpath temporary filename."""
    mkDirP(tempFileDirectory)
    return os.path.join(
        *temporarySplitFileName(tempFileDirectory)
    )


def flushFsDeleteQueue(fsDeleteQueue):
    """ Assuming all commits of a delete operation have been
        issued, given a list of actual filenames
        to delete (already unregistered from the db-fs),
        perform the actual deletions.
    """
    for physicalFileToDelete in fsDeleteQueue:
        if os.path.isfile(physicalFileToDelete):
            os.remove(physicalFileToDelete)


def mkDirP(dName):
    """Mimic 'mkdir -p DIRNAME' in creating the full path."""
    nDir = os.path.normpath(os.path.abspath(dName))
    if not os.path.isdir(nDir):
        pth, last = os.path.split(nDir)
        mkDirP(pth)
        os.mkdir(nDir)


def isWritableDirectory(fullDirPath):
    """ Is this a writable directory?

        NOTE:   this function happens to create the
                directory if it does not exist
    """
    try:
        if not os.path.exists(fullDirPath):
            mkDirP(fullDirPath)
        #
        if not os.path.isdir(fullDirPath):
            return False
        else:
            # permission check
            return os.access(fullDirPath, os.X_OK | os.W_OK)
    except Exception as e:
        # a rather rough way to silence any filesystem errors
        return False


def makeSymlink(src, dest):
    """
        Create a symlink as instructed
        and return the destination path
    """
    os.symlink(src, dest)
    return dest
